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
from bpy.props import EnumProperty

class NODEUTILS_PT_main_panel(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_label = 'Node Utils'
    bl_category = 'Group'
    
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True) 
        row.operator('nd_utils.select_reroutes')
        layout.separator()

        layout.label(text="Normalize Node Width:")
        box = layout.box()
        op_props = box.row(align=True).operator('nd_utils.normalize_node_width', text='Normalize by Max')
        op_props.normalize_type = "MAX"

        op_props = box.row(align=True).operator('nd_utils.normalize_node_width', text='Normalize by Min')
        op_props.normalize_type = "MIN"

        op_props = box.row(align=True).operator('nd_utils.normalize_node_width', text='Normalize by Average')
        op_props.normalize_type = "AVERAGE"

def get_nodes(context):
    tree = context.space_data.node_tree

    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree.nodes

class NODEUTILS_OT_SELECT_REROUTES(bpy.types.Operator):
    bl_label = "Select All Reroutes"
    bl_idname = "nd_utils.select_reroutes"
    bl_description = "Aligns nodes by their leftmost edge"
    bl_options = {'REGISTER', 'UNDO_GROUPED'} 

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid_trees = ("ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree", "GeometryNodeTree")
        is_valid = space.type == 'NODE_EDITOR' and space.node_tree is not None and space.tree_type in valid_trees
        return is_valid

    def execute(self, context):
        nodes = get_nodes(context)
        reroutes = tuple(node for node in nodes if node.type == 'REROUTE')
        
        if not reroutes:
            return {'CANCELLED'}
        
        for node in nodes:
            node.select = True if node.type == 'REROUTE' else False
        return {'FINISHED'}

class NODEUTILS_OT_NORMALIZE_NODE_WIDTH(bpy.types.Operator):
    bl_label = "Normalize Node Width"
    bl_idname = "nd_utils.normalize_node_width"
    bl_description = "Sets uniform width for selected nodes"
    bl_options = {'REGISTER', 'UNDO'} 

    normalize_type: EnumProperty(name='normalize_type', items=(
        ('MAX', 'MAX', ''), ('MIN', 'MIN', ''), ('AVERAGE', 'AVERAGE', ''),))
    desc_dict = {'MAX':'maximum','MIN':'minimum','AVERAGE':'average',}

    @classmethod
    def description(self, context, props):
        return f"Sets width to selected nodes according to their {self.desc_dict[props.normalize_type]}"

    @classmethod
    def poll(cls, context):
        space = context.space_data
        valid_trees = ("ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree", "GeometryNodeTree")
        is_valid = space.type == 'NODE_EDITOR' and space.node_tree is not None and space.tree_type in valid_trees
        return is_valid

    def execute(self, context):
        selected_nodes = tuple(node for node in get_nodes(context) if (node.select and node.type != 'FRAME' and node.type != 'REROUTE'))
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

classes = (
    NODEUTILS_PT_main_panel,
    NODEUTILS_OT_SELECT_REROUTES,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
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