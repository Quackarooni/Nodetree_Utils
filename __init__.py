# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name": "Nodetree Utils",
    "description": "Quality of life shortcuts for nodetrees",
    "author": "Quackers",
    "version": (1, 0),
    "blender": (2, 83, 0),
    "location": "Node Editor > N Panel > Group",
    "category": "Node",
}

import bpy
from bpy.props import EnumProperty, StringProperty

#adapted from https://github.com/valcohen/tidy_group_inputs/blob/master/vbc_tidy_group_inputs.py
class NODEUTILS_PT_main_panel(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'Node Utils'
    bl_category = 'Group'
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Select by Type:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.select_by_type', text='Nodes')
        op_props.select_type = "NODES"
        op_props = row.operator('nd_utils.select_by_type', text='Reroutes')
        op_props.select_type = "REROUTES"
        op_props = row.operator('nd_utils.select_by_type', text='Frames')
        op_props.select_type = "FRAMES"

        layout.label(text="Normalize Node Width:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.normalize_node_width', text='By Max')
        op_props.normalize_type = "MAX"

        op_props = row.operator('nd_utils.normalize_node_width', text='By Min')
        op_props.normalize_type = "MIN"

        op_props = row.operator('nd_utils.normalize_node_width', text='By Average')
        op_props.normalize_type = "AVERAGE"

        layout.label(text="Label Reroutes by Socket:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.label_reroutes', text='By Input')
        op_props = row.operator('nd_utils.label_reroutes', text='By Output')        

        layout.row().operator('nd_utils.batch_label')
        layout.row().operator('nd_utils.recenter_nodes')


def get_nodes(context):
    tree = context.space_data.node_tree

    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree.nodes

class NodeUtilsBase:
    bl_label = "Nodeutils Baseclass"
    bl_options = {'REGISTER', 'UNDO'} 

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid_trees = ("ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree", "GeometryNodeTree")
        is_valid = space.type == 'NODE_EDITOR' and space.node_tree is not None and space.tree_type in valid_trees
        return is_valid


class NODEUTILS_OT_SELECT_BY_TYPE(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Select By Type"
    bl_idname = "nd_utils.select_by_type"
    bl_description = "Select by specific node type"

    select_type: EnumProperty(name='normalize_type', items=(
        ('NODES', 'NODES', ''), ('REROUTES', 'REROUTES', ''), ('FRAMES', 'FRAMES', ''),))

    @classmethod
    def description(self, context, props):
        return f"Selects all {props.select_type.lower()}"

    def execute(self, context):
        nodes = get_nodes(context)
        
        if self.select_type == 'NODES':
            def check_condition(node_type):
                return node_type not in ('REROUTE', 'FRAME')     
        elif self.select_type == 'REROUTES':
            def check_condition(node_type):
                return node_type == 'REROUTE'
        elif self.select_type == 'FRAMES':
            def check_condition(node_type):
                return node_type == 'FRAME'
        
        nodes_to_select = tuple(node for node in nodes if check_condition(node.bl_static_type))
        will_selection_be_identical = all(node.select if check_condition(node.bl_static_type) else (not node.select) for node in nodes)
        
        if not nodes_to_select or will_selection_be_identical:
            return {'CANCELLED'}

        for node in nodes:
            node.select = True if check_condition(node.bl_static_type) else False
        return {'FINISHED'}


class NODEUTILS_OT_NORMALIZE_NODE_WIDTH(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Normalize Node Width"
    bl_idname = "nd_utils.normalize_node_width"
    bl_description = "Sets uniform width for selected nodes"

    normalize_type: EnumProperty(name='normalize_type', items=(
        ('MAX', 'MAX', ''), ('MIN', 'MIN', ''), ('AVERAGE', 'AVERAGE', ''),))
    desc_dict = {'MAX':'maximum','MIN':'minimum','AVERAGE':'average',}

    @classmethod
    def description(self, context, props):
        return f"Sets width to selected nodes according to their {self.desc_dict[props.normalize_type]}"

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type != 'FRAME' and node.bl_static_type != 'REROUTE'))
        if len(selected_nodes) <= 1:
            return {'CANCELLED'}

        node_widths = set(node.dimensions.x for node in selected_nodes)
        if self.normalize_type == 'AVERAGE':
            width_to_set = sum(node_widths)/len(node_widths)
        else:
            width_to_set = min(node_widths) if self.normalize_type == 'MIN' else max(node_widths)

        if all(width_to_set == node.width for node in selected_nodes):
            return {'CANCELLED'}

        for node in selected_nodes:
            node.width = width_to_set
        return {'FINISHED'}


class NODEUTILS_OT_BATCH_LABEL(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Batch Label"
    bl_idname = "nd_utils.batch_label"
    bl_description = "Renames all selected nodes according to specified label"

    label: StringProperty(name='', default='')
  
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if tuple(node for node in get_nodes(context) if node.select):
            row.label(icon='NODE')
            row.prop(self, "label")
        else:
            row.label(icon='ERROR')
            row.label(text='No nodes selected')           

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if node.select)

        for node in selected_nodes:
            node.label = self.label

        self.label = ''
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_popup(self, event)


class NODEUTILS_OT_LABEL_REROUTES(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Label Reroutes"
    bl_idname = "nd_utils.label_reroutes"
    bl_description = "Labels selected reroutes based on their input/output"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    label: StringProperty(name='', default='')
  
    def check_parent_label(self, node, level=0):
        if level >= 100:
            return ['RECURSION ERROR']
        for socket in node.inputs:
            if node.label != '' or len(socket.links) == 0 or not node.select:
                return node.label

            link = socket.links[0]
            if (link.from_node.bl_static_type != 'REROUTE'):
                return link.from_socket.name
            
            label = link.from_node.label
            if label != '':
                return label
            return self.check_parent_label(link.from_node, level=level+1)


    def execute(self, context):
        init_reroutes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type == 'REROUTE'))
        reroutes = sorted(init_reroutes, key=lambda n: n.location.x)
        if not reroutes:
            return {'CANCELLED'}

        old_labels = [reroute.label for reroute in reroutes]
        new_labels = []
        for reroute in reroutes:
            new_label = self.check_parent_label(reroute)
            if new_label == ['RECURSION ERROR']:
                self.report({'ERROR'}, "RECURSION_ERROR: Exceeded recursion limit. \nTry again with a smaller selection, or make sure input-to-output goes left-to-right.")
                return {'CANCELLED'}
            reroute.label = new_label
            new_labels.append(new_label)

        if (old_labels == new_labels):
            return {'CANCELLED'}
        return {'FINISHED'}

class NODEUTILS_OT_RECENTER_NODES(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Recenter Nodes"
    bl_idname = "nd_utils.recenter_nodes"
    bl_description = "Places selected nodes such that their middle point is at the origin"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        nodes = tuple(node for node in get_nodes(context))
        if not nodes:
            return {'CANCELLED'}
        
        
        for index, node  in enumerate(nodes):
            if index == 0:
                most_left = node.location.x
                most_right = node.location.x + node.dimensions.x
                most_top = node.location.y
                most_bottom = node.location.y + node.dimensions.y
                continue
            
            most_left = min(most_left, node.location.x)
            most_right = max(most_right, node.location.x + node.dimensions.x)
            most_top = max(most_top, node.location.y)
            most_bottom = min(most_bottom, node.location.y + node.dimensions.y)

        midpoint_x = 0.5*(most_left+most_right)
        midpoint_y = 0.5*(most_top+most_bottom)

        for node in nodes:
            node.location.x -= midpoint_x
            node.location.y -= midpoint_y
        return {'FINISHED'}

classes = (
    NODEUTILS_PT_main_panel,
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES

)

addon_keymaps = []
keymap_defs = ()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    ''' 
    addon_keymaps.clear()
    if key_config := bpy.context.window_manager.keyconfigs.addon:
        for operator, key in keymap_defs:
            key_map = key_config.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
            key_entry = key_map.keymap_items.new(operator, key, value='PRESS')

            addon_keymaps.append((key_map, key_entry))'''
    
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    '''
    for key_map, key_entry in addon_keymaps:
        key_map.keymap_items.remove(key_entry)
    addon_keymaps.clear()
    '''

if __name__ == '__main__':
    register()