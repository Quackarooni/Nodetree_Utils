import bpy
from bpy.props import EnumProperty, BoolProperty, IntVectorProperty
from .keymaps import addon_keymaps
import rna_keymap_ui

class NodetreeUtilsPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def draw(self, context):
        layout = self.layout
        keymap_spacing = 0.15

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

        for km, kmi in get_kmi_l:
            if not km.name == old_km_name:
                col.label(text=str(km.name), icon="DOT")
            col.context_pointer_set("keymap", km)
            if kmi.idname in ('nd_align.center', 'nd_align.middle'):
                if not self.hide_center_and_middle:
                    rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
                    col.separator(factor=keymap_spacing)
            else:
                rna_keymap_ui.draw_kmi([], kc, km, kmi, col, 0)
                col.separator(factor=keymap_spacing)
            old_km_name = km.name


def register():
    bpy.utils.register_class(NodetreeUtilsPreferences)

def unregister():
    bpy.utils.unregister_class(NodetreeUtilsPreferences)