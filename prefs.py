import bpy
from bpy.props import EnumProperty, BoolProperty, IntVectorProperty
from .keymaps import addon_keymaps
import rna_keymap_ui

class NodetreeUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    use_unique: BoolProperty(
        name="Use Unique Values",
        default=True,
        description="Toggles whether Normalize Width only uses unique with values for its calculations")
    
    ignore_empty_selections: BoolProperty(
        name="Ignore Empty Selections",
        default=True,
        description="Ignores selection by type for New and Intersect when resulting selection is empty")
    
    display_switch_buttons: BoolProperty(
        name="Display Switch Buttons",
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
        col.prop(self, "use_unique")
        col.prop(self, "ignore_empty_selections")
        col.prop(self, "display_switch_buttons")
        col.prop(self, "display_mode")

        col = layout.box().column()
        col.label(text="Keymap List:", icon="KEYINGSET")

        kc = bpy.context.window_manager.keyconfigs.user
        old_km_name = ""
        get_kmi_l = []
        for km_add, kmi_add in reversed(addon_keymaps):
            for km_con in kc.keymaps:
                if km_add.name == km_con.name:
                    km = km_con
                    break

            for kmi_con in km.keymap_items:
                if kmi_add.idname == kmi_con.idname:
                    if kmi_add.name == kmi_con.name:
                        get_kmi_l.append((km, kmi_con))

        get_kmi_l = sorted(set(get_kmi_l), key=get_kmi_l.index)

        old_kmi_name = ''
        is_first_entry = True
        group_spacing = 0.5

        for km, kmi in get_kmi_l:
            if not kmi.name == old_kmi_name:
                if not is_first_entry:
                    col.separator(factor=group_spacing)
                col.label(text=str(kmi.name), icon="DOT")

            col.context_pointer_set("keymap", km)
            
            rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
            col.separator(factor=keymap_spacing)
            old_kmi_name = kmi.name
            is_first_entry = False


def register():
    bpy.utils.register_class(NodetreeUtilsPreferences)

def unregister():
    bpy.utils.unregister_class(NodetreeUtilsPreferences)