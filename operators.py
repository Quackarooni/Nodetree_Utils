
import bpy
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty, IntProperty
import itertools
from pathlib import Path

def get_nodes(context):
    tree = context.space_data.node_tree
    fetch_user_preferences()
    if tree.nodes.active:
        while tree.nodes.active != context.active_node:
            tree = tree.nodes.active.node_tree

    return tree.nodes

def fetch_user_preferences():
    ADD_ON_PATH = Path(__file__).parent.name
    return bpy.context.preferences.addons[ADD_ON_PATH].preferences

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
        prefs = fetch_user_preferences()
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

        if prefs.ignore_empty_selections:
            if (selection_mode == "New" or selection_mode == "Intersection") and not nodes_to_select:
                self.report({'INFO'}, f'No {self.select_target.lower()} found. Ignoring selection.')
                return {'CANCELLED'}
        will_selection_be_identical = nodes_to_select == selected_nodes
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
        prefs = fetch_user_preferences()
        selected_nodes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type != 'FRAME' and node.bl_static_type != 'REROUTE'))
        if len(selected_nodes) <= 1:
            return {'CANCELLED'}

        width_init = (node.dimensions.x for node in selected_nodes)
        node_widths = set(width_init)if prefs.use_unique else tuple(width_init)

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
  
    check_by: EnumProperty(name='check_by', items=(
        ('INPUT', 'INPUT', ''), ('OUTPUT', 'OUTPUT', ''),))

    @classmethod
    def description(self, context, props):
        if props.check_by == "INPUT":
            msg_end = "input"
        else:
            msg_end = f"most recently connected {props.check_by.lower()}"

        return f"Labels selected reroutes based on their {msg_end} link"

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

    def check_child_label(self, node, level=0):
        if level >= 100:
            return ['RECURSION ERROR']
        for socket in node.outputs:
            if node.label != '' or len(socket.links) == 0 or not node.select:
                return node.label

            link = socket.links[-1]
            if (link.to_node.bl_static_type != 'REROUTE'):
                return link.to_socket.name
            
            label = link.to_node.label
            if label != '':
                return label
            return self.check_child_label(link.to_node, level=level+1)


    def execute(self, context):
        use_inputs = self.check_by == "INPUT"

        init_reroutes = tuple(node for node in get_nodes(context) if (node.select and node.bl_static_type == 'REROUTE'))
        reroutes = sorted(init_reroutes, key=lambda n: n.location.x, reverse=(not use_inputs))
        if not reroutes:
            return {'CANCELLED'}

        old_labels = [reroute.label for reroute in reroutes]
        new_labels = []
        for reroute in reroutes:
            if use_inputs:
                new_label = self.check_parent_label(reroute)
            else:
                new_label = self.check_child_label(reroute)

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
    bl_options = {'REGISTER'}

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

class NODEUTILS_OT_TOGGLE_SELECT_TYPE(bpy.types.Operator, NodeUtilsBase):
    bl_label = "Switch Select Type"
    bl_idname = "nd_utils.switch_select_type"
    bl_description = "Switches the select type according to specified option"
    

    switch_mode: EnumProperty(name='sockets_to_hide', items=(
        ('SWITCH_TO_FIRST', 'SWITCH_TO_FIRST', ''), 
        ('SWITCH_TO_LAST', 'SWITCH_TO_LAST', ''), 
        ('CYCLE_UP', 'CYCLE_UP', ''), 
        ('CYCLE_DOWN', 'CYCLE_DOWN', ''),))

    def execute(self, context):
        selection_enum = context.window_manager.nd_utils_props
        enum_items = selection_enum.bl_rna.properties['selection_mode'].enum_items
        current_select_mode = selection_enum.selection_mode

        if not self.switch_mode.startswith('CYCLE'):
            if self.switch_mode == 'SWITCH_TO_FIRST':
                new_select_mode = enum_items[0].identifier
            elif self.switch_mode == 'SWITCH_TO_LAST':
                new_select_mode = enum_items[-1].identifier

            selection_enum.selection_mode = new_select_mode
            return {'CANCELLED'}

        enum_dict = {}
        for item in enum_items:
            if item.identifier == current_select_mode:
                current_select_id = item.value
            enum_dict[item.value] = item.identifier

        if self.switch_mode == "CYCLE_UP":
            new_select_id = max(current_select_id - 1, 0)
        elif self.switch_mode == "CYCLE_DOWN":
            new_select_id = min(current_select_id + 1, len(enum_items) - 1)
            
        new_select_mode = enum_dict.get(new_select_id)
        selection_enum.selection_mode = new_select_mode
        return {'CANCELLED'}

class NodetreeUtilsProperties(bpy.types.PropertyGroup):
    selection_mode: EnumProperty(name='Selection Mode', description='Toggles what mode of selection is used.',default='New', items=(
        ('New', 'New', 'Creates a new selection out of the specified nodes', 'SELECT_SET', 0),
        ('Add', 'Add', 'Adds specified nodes from current selection', 'SELECT_EXTEND', 1), 
        ('Subtract', 'Subtract', 'Removes specified nodes from current selection', 'SELECT_SUBTRACT', 2), 
        ('Intersection', 'Intersection', 'Only selects nodes shared between specified nodes and current selection','SELECT_INTERSECT', 3),
        ('Invert', 'Invert', 'Flip the selection state of the specified nodes','SELECT_DIFFERENCE', 4),
        ))

classes = (
    NodetreeUtilsProperties,
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_SET_WIDTH,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES,
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS,
    NODEUTILS_OT_TOGGLE_SELECT_TYPE
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.WindowManager.nd_utils_props = bpy.props.PointerProperty(type=NodetreeUtilsProperties)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    del bpy.types.WindowManager.nd_utils_props 