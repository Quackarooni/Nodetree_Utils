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
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS
)

class NODEUTILS_PT_main_panel(Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'Node Utils'
    bl_category = 'Utils'
    
    def draw(self, context):
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

        layout.row().operator('nd_utils.batch_label')
        layout.row().operator('nd_utils.set_node_width')
        layout.row().operator('nd_utils.recenter_nodes')

def register():
    bpy.utils.register_class(NODEUTILS_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(NODEUTILS_PT_main_panel)