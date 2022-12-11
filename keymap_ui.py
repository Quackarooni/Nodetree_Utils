from rna_keymap_ui import _indented_layout, draw_km
import bpy

def draw_kmi(display_keymaps, kc, km, kmi, layout, level, label=''):
    map_type = kmi.map_type

    col = _indented_layout(layout, level)

    if kmi.show_expanded:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    # header bar
    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    if km.is_modal:
        row.separator()
        row.prop(kmi, "propvalue", text="")
    else:
        label = kmi.name if label == '' else label
        row.label(text=label)

    row = split.row()
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")
    else:
        row.label()

    if (not kmi.is_user_defined) and kmi.is_user_modified:
        row.operator("preferences.keyitem_restore", text="", icon='BACK').item_id = kmi.id
    else:
        row.operator(
            "preferences.keyitem_remove",
            text="",
            # Abusing the tracking icon, but it works pretty well here.
            icon=('TRACKING_CLEAR_BACKWARDS' if kmi.is_user_defined else 'X')
        ).item_id = kmi.id

    # Expanded, additional event settings
    if kmi.show_expanded:
        box = col.box()

        split = box.split(factor=0.4)
        sub = split.row()

        if km.is_modal:
            sub.prop(kmi, "propvalue", text="")
        else:
            # One day...
            # sub.prop_search(kmi, "idname", bpy.context.window_manager, "operators_all", text="")
            sub.prop(kmi, "idname", text="")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            # Use `*_ui` properties as integers aren't practical.
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)

            subrow.prop(kmi, "key_modifier", text="", event=True)

        # Operator properties
        box.template_keymap_item_properties(kmi)

        # Modal key maps attached to this operator
        if not km.is_modal:
            kmm = kc.keymaps.find_modal(kmi.idname)
            if kmm:
                draw_km(display_keymaps, kc, kmm, None, layout, level + 1)
                layout.context_pointer_set("keymap", km)

def draw_keyboard_shorcuts(layout, spacing, keymaps, display):
    col = layout.box().column()
    col.label(text="Keymap List:", icon="KEYINGSET")

    kc = bpy.context.window_manager.keyconfigs.user
    get_kmi_l = []
    labels = {}
    for km_add, kmi_add, label in reversed(keymaps):
        for km_con in kc.keymaps:
            if km_add.name == km_con.name:
                km = km_con
                break    

        for kmi_con in km.keymap_items:
            if kmi_add.idname == kmi_con.idname:
                if kmi_add.name == kmi_con.name:
                    get_kmi_l.append((km, kmi_con))
                    label_list = labels.get(kmi_con.name, [])
                    if (label not in label_list):
                        label_list.append(label)
                    labels[kmi_con.name] = label_list

    get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)
    old_category = ''
    old_label = ''
    is_first_entry = True
    group_spacing = 0.35

    for km, kmi in get_kmi_l:
        curr_category = display[kmi.name]
        if curr_category is None:
            curr_category = kmi.name

        if not curr_category == old_category:
            if not is_first_entry:
                col.separator(factor=group_spacing)
            col.label(text=str(curr_category), icon="DOT")

        col.context_pointer_set("keymap", km)
        
        #rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
        label_list = labels[kmi.name]
        if len(label_list) == 1:
            label = label_list[0]
        else:
            label = label_list.pop(0)

        if old_label != label:
            draw_kmi([], kc, km, kmi, col, 0, label=label)
            col.separator(factor=spacing)
        old_category = curr_category
        old_label = label
        is_first_entry = False