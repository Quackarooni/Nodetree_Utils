import bpy

from bpy.types import Panel
from .operators import (
    NodetreeUtilsProperties,
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_SET_WIDTH,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES,
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS,
    NODEUTILS_OT_TOGGLE_SELECT_TYPE,
    fetch_user_preferences
)

class NODEUTILS_PT_main_panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'Node Utils'
    bl_category = 'Utils'
    
    def draw(self, context):
        prefs = fetch_user_preferences()

        layout = self.layout
        layout.label(text="Select by Type:")
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Selection Mode:")
        col.separator(factor=0.5)
        col.prop(context.window_manager.nd_utils_props, "selection_mode", text="")
        row = box.row(align=True)
        op_props = row.operator('nd_utils.select_by_type', text='Nodes')
        op_props.select_target = "NODES"
        op_props = row.operator('nd_utils.select_by_type', text='Reroutes')
        op_props.select_target = "REROUTES"
        op_props = row.operator('nd_utils.select_by_type', text='Frames')
        op_props.select_target = "FRAMES"


        if prefs.display_switch_buttons:
            col = box.column(align=True)
            col.label(text="Switch Selection Mode:")
            col.separator(factor=0.5)

            row = col.row(align=True)
            row.alignment = 'EXPAND' if (prefs.display_mode != 'ICON') else 'CENTER'
            switch_names = ('First', 'Last', 'Cycle Up', 'Cycle Down') if (prefs.display_mode != 'ICON') else ['']*4
            switch_icons = ('TRIA_UP_BAR', 'TRIA_DOWN_BAR', 'TRIA_UP', 'TRIA_DOWN') if (prefs.display_mode != 'TEXT') else ['NONE']*4
            switch_props = ('SWITCH_TO_FIRST', 'SWITCH_TO_LAST', 'CYCLE_UP', 'CYCLE_DOWN',)
            for name, icon, prop in zip(switch_names, switch_icons, switch_props):
                op_props = row.operator('nd_utils.switch_select_type', text=name, icon=icon)
                op_props.switch_mode = prop

        layout.label(text="Normalize Node Width:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.normalize_node_width', text='By Max')
        op_props.normalize_type = "MAX"

        op_props = row.operator('nd_utils.normalize_node_width', text='By Min')
        op_props.normalize_type = "MIN"

        op_props = row.operator('nd_utils.normalize_node_width', text='By Average')
        op_props.normalize_type = "AVERAGE"

        layout.label(text="Toggle Unused Sockets:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.toggle_unused_sockets', text='Inputs')
        op_props.sockets_to_hide = "INPUT"
        op_props = row.operator('nd_utils.toggle_unused_sockets', text='Outputs')
        op_props.sockets_to_hide = "OUTPUT"

        layout.label(text="Label Reroutes by Links:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.label_reroutes', text='By Input')
        op_props.check_by = "INPUT"
        op_props = row.operator('nd_utils.label_reroutes', text='By Output')        
        op_props.check_by = "OUTPUT"

        layout.label(text="Batch Operations:")
        spacing = 0.25
        col = layout.box().column(align=True)
        col.operator('nd_utils.batch_label', text='Set Labels')
        col.separator(factor=spacing)
        col.operator('nd_utils.set_node_width')
        col.separator(factor=spacing)
        col.operator('nd_utils.recenter_nodes', text='Center at Origin')

        

def register():
    bpy.utils.register_class(NODEUTILS_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(NODEUTILS_PT_main_panel)