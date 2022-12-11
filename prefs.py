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


    custom_color: bpy.props.FloatVectorProperty (
        name = "Custom Color",
        description = "Color property for the Set Color Operator",
        subtype = 'COLOR_GAMMA',
        min = 0, max = 1,
        default = [0.1,0.3,0.5]
    )

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
        
        keymap_ui.draw_keyboard_shorcuts(
            layout=layout, spacing=keymap_spacing, keymaps=addon_keymaps, display=prefs_display)

def register():
    bpy.utils.register_class(NodetreeUtilsPreferences)

def unregister():
    bpy.utils.unregister_class(NodetreeUtilsPreferences)