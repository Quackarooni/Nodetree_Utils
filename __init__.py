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
from bpy.props import EnumProperty, StringProperty, IntProperty
import itertools

#adapted from https://github.com/valcohen/tidy_group_inputs/blob/master/vbc_tidy_group_inputs.py
class NODEUTILS_PT_main_panel(bpy.types.Panel):
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

        layout.label(text="Label Reroutes by Socket: (WIP)")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.label_reroutes', text='By Input')
        op_props = row.operator('nd_utils.label_reroutes', text='By Output')        

        layout.label(text="Toggle Unused Sockets:")
        row = layout.box().row(align=True)
        op_props = row.operator('nd_utils.toggle_unused_sockets', text='Inputs')
        op_props.sockets_to_hide = "INPUT"
        op_props = row.operator('nd_utils.toggle_unused_sockets', text='Outputs')
        op_props.sockets_to_hide = "OUTPUT"

        layout.row().operator('nd_utils.batch_label')
        layout.row().operator('nd_utils.set_node_width')
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

    select_target: EnumProperty(name='select_target', items=(
        ('NODES', 'NODES', ''), ('REROUTES', 'REROUTES', ''), ('FRAMES', 'FRAMES', ''),))
    @classmethod
    def description(self, context, props):
        return f"Targets {props.select_target.lower()} for selection"

    def execute(self, context):
        selection_mode = context.window_manager.nd_utils_props.selection_mode
        nodes = get_nodes(context)
        selected_nodes = set(node for node in nodes if node.select)

        if self.select_target == 'NODES':
            def check_condition(node_type):
                return node_type not in ('REROUTE', 'FRAME')     
        elif self.select_target == 'REROUTES':
            def check_condition(node_type):
                return node_type == 'REROUTE'
        elif self.select_target == 'FRAMES':
            def check_condition(node_type):
                return node_type == 'FRAME'
        
        nodes_of_spec_type = set(node for node in nodes if check_condition(node.bl_static_type))
        
        if selection_mode == 'New':
            nodes_to_select = nodes_of_spec_type
        elif selection_mode == 'Add':
            nodes_to_select = selected_nodes.union(nodes_of_spec_type)
        elif selection_mode == 'Subtract':
            nodes_to_select = selected_nodes.difference(nodes_of_spec_type)
        elif selection_mode == 'Intersection':
            nodes_to_select = selected_nodes.intersection(nodes_of_spec_type)
        elif selection_mode == 'Invert':
            nodes_to_select = selected_nodes.symmetric_difference(nodes_of_spec_type)
        else:
            return {'CANCELLED'}

        will_selection_be_identical = nodes_to_select == selected_nodes
        if (selection_mode == "New" or selection_mode == "Intersection") and not nodes_to_select:
            self.report({'INFO'}, f'No {self.select_target.lower()} found. Ignoring selection.')
            return {'CANCELLED'}
        if will_selection_be_identical:
            return {'CANCELLED'}

        for node in nodes:
            node.select = False
        for node in nodes_to_select:
            node.select = True

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

class NODEUTILS_OT_SET_WIDTH(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Set Node Width"
    bl_idname = "nd_utils.set_node_width"
    bl_description = "Resizes all selected nodes according to specified width"

    width: IntProperty(name='', default=30, min=30)
    last_resized_nodes = []
  
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if tuple(node for node in get_nodes(context) if node.select):
            row.label(icon='NODE')
            row.prop(self, "width")
        else:
            row.label(icon='ERROR')
            row.label(text='No nodes selected')           

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if node.select)
        for node in selected_nodes:
            node.width = self.width

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
    bl_description = "Repositions nodetree such that its midpoint is at the origin"
    bl_options = {'REGISTER', 'UNDO_GROUPED'}

    def execute(self, context):
        nodes = tuple(node for node in get_nodes(context))
        if not nodes:
            return {'CANCELLED'}
        
        for index, node in enumerate(nodes):
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

        midpoint_x = 0.5*(most_left + most_right)
        midpoint_y = 0.5*(most_top + most_bottom)

        if midpoint_x == 0 and midpoint_y == 0:
            return {'CANCELLED'}

        for node in nodes:
            node.location.x -= midpoint_x
            node.location.y -= midpoint_y
        return {'FINISHED'}

class NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Toggle Unused Sockets"
    bl_idname = "nd_utils.toggle_unused_sockets"
    bl_description = "Toggles the visibility of unconnected node sockets"

    sockets_to_hide: EnumProperty(name='sockets_to_hide', items=(
        ('INPUT', 'INPUT', ''), ('OUTPUT', 'OUTPUT', ''),))

    @classmethod
    def description(self, context, props):
        return f"Toggles the visibility of unconnected {props.sockets_to_hide.lower()} sockets"

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type != 'FRAME' and node.bl_static_type != 'REROUTE'))
        
        if self.sockets_to_hide == 'INPUT':
            all_sockets = itertools.chain.from_iterable(
                (socket for socket in node.inputs) for node in selected_nodes)
        else:
            all_sockets = itertools.chain.from_iterable(
                (socket for socket in node.outputs) for node in selected_nodes)

        unused_sockets = tuple(socket for socket in all_sockets if socket.enabled and not socket.is_linked)
        if len(unused_sockets) <= 0:
            return {'CANCELLED'}

        toggle_value = any(not socket.hide for socket in unused_sockets)
        for socket in unused_sockets:
            socket.hide = toggle_value
        return {'FINISHED'}
class NodetreeUtilsProperties(bpy.types.PropertyGroup):
    selection_mode: EnumProperty(name='Selection Mode', description='Toggles what mode of selection is used.',default='New', items=(
        ('New', 'New', 'Creates a new selection out of the specified nodes', 'SELECT_SET', 0),
        ('Add', 'Add', 'Adds specified nodes from current selection', 'SELECT_EXTEND', 1), 
        ('Subtract', 'Subtract', 'Removes specified nodes from current selection', 'SELECT_SUBTRACT', 2), 
        ('Intersection', 'Intersection', 'Only selects nodes shared between specified nodes and current selection','SELECT_INTERSECT', 3),
        ('Invert', 'Invert', 'Flip the selection state of the specified nodes','SELECT_DIFFERENCE', 4)
        ))

classes = (
    NodetreeUtilsProperties,
    NODEUTILS_PT_main_panel,
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_SET_WIDTH,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES,
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS
)

addon_keymaps = []
keymap_defs = ()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    bpy.types.WindowManager.nd_utils_props = bpy.props.PointerProperty(type=NodetreeUtilsProperties)
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
    
    del bpy.types.WindowManager.nd_utils_props 
    '''
    for key_map, key_entry in addon_keymaps:
        key_map.keymap_items.remove(key_entry)
    addon_keymaps.clear()
    '''

if __name__ == '__main__':
    register()