import bpy
from bpy.props import EnumProperty, BoolProperty, IntVectorProperty
from .keymaps import addon_keymaps, prefs_display
from . import keymap_ui

class NodetreeUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    use_unique: BoolProperty(
        name="Normalize by Unique Values",
        default=True,
        description="Toggles whether Normalize Width ignores repeated width values for its calculations")
    
    ignore_empty_selections: BoolProperty(
        name="Ignore Empty Selections",
        default=True,
        description="Ignores selection by type for New and Intersect when resulting selection is empty")
    
    display_switch_buttons: BoolProperty(
        name="Display Selection Type Switches",
        default=True,
        description="Display buttons for switching selection types")

    display_mode: EnumProperty(
        name="Display Mode",
        items=(
            ("ICON", "Icon", "Display buttons as icons"),
            ("TEXT", "Text", "Display buttons as text"),
            ("TEXT AND ICON", "Text and Icon", "Display buttons as text and icons")
        ),
        default="TEXT AND ICON",
        description="Specifies how to display switch buttons are displayed")

    def draw(self, context):
        layout = self.layout
        keymap_spacing = 0.15

        col = layout.row().column(heading="Options:")
        col.prop(self, "ignore_empty_selections")
        col.prop(self, "use_unique")
        row = col.row()
        row.prop(self, "display_switch_buttons")
        split = row.split()
        split.alignment = 'RIGHT'
        split.prop(self, "display_mode", text='')

        col = layout.box().column()
        col.label(text="Keymap List:", icon="KEYINGSET")

        kc = bpy.context.window_manager.keyconfigs.user
        get_kmi_l = []
        labels = {}
        for km_add, kmi_add, label in reversed(addon_keymaps):
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
            curr_category = prefs_display[kmi.name]
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
                keymap_ui.draw_kmi([], kc, km, kmi, col, 0, label=label)
            col.separator(factor=keymap_spacing)
            old_category = curr_category
            old_label = label
            is_first_entry = False


def register():
    bpy.utils.register_class(NodetreeUtilsPreferences)

def unregister():
    bpy.utils.unregister_class(NodetreeUtilsPreferences)