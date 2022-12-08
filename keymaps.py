import bpy
from .operators import (
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_SET_WIDTH,
    NODEUTILS_OT_SET_COLOR,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES,
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS,
    NODEUTILS_OT_SWITCH_SELECT_TYPE,
    NODEUTILS_OT_SWITCH_VIEWER_DOMAIN,
    NODEUTILS_OT_PIE_MENU_SWITCH_VIEWER_DOMAIN,
    NODEUTILS_MT_SWITCH_VIEWER_DOMAIN_OPTIONS,
    NODEUTILS_OT_SWITCH_VIEWER_DOMAIN_INVOKE_MENU,
)

addon_keymaps = []
prefs_display = {}
keymap_defs = (
    (NODEUTILS_OT_SELECT_BY_TYPE.bl_idname, 'NONE', None, 'Select Nodes', False, (('select_target', 'NODES'),)),
    (NODEUTILS_OT_SELECT_BY_TYPE.bl_idname, 'NONE', None, 'Select Reroutes', False, (('select_target', 'REROUTES'),)),
    (NODEUTILS_OT_SELECT_BY_TYPE.bl_idname, 'NONE', None, 'Select Frames', False, (('select_target', 'FRAMES'),)),
    (NODEUTILS_OT_SWITCH_SELECT_TYPE.bl_idname, 'NONE', None, 'Switch to First', False, (('switch_mode', 'SWITCH_TO_FIRST'),)),
    (NODEUTILS_OT_SWITCH_SELECT_TYPE.bl_idname, 'NONE', None, 'Switch to Last', False, (('switch_mode', 'SWITCH_TO_LAST'),)),
    (NODEUTILS_OT_SWITCH_SELECT_TYPE.bl_idname, 'NONE', None, 'Cycle Up', True, (('switch_mode', 'CYCLE_UP'),)),
    (NODEUTILS_OT_SWITCH_SELECT_TYPE.bl_idname, 'NONE', None, 'Cycle Down', True, (('switch_mode', 'CYCLE_DOWN'),)),
    (NODEUTILS_OT_NORMALIZE_NODE_WIDTH.bl_idname, 'NONE', None, 'By Max', False, (('normalize_type', 'MAX'),)),
    (NODEUTILS_OT_NORMALIZE_NODE_WIDTH.bl_idname, 'NONE', None, 'By Min', False, (('normalize_type', 'MIN'),)),
    (NODEUTILS_OT_NORMALIZE_NODE_WIDTH.bl_idname, 'NONE', None, 'By Average', False, (('normalize_type', 'AVERAGE'),)),
    (NODEUTILS_OT_LABEL_REROUTES.bl_idname, 'NONE', None, 'By Input', False, (('check_by', 'INPUT'),)),
    (NODEUTILS_OT_LABEL_REROUTES.bl_idname, 'NONE', None, 'By Output', False, (('check_by', 'OUTPUT'),)),
    (NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS.bl_idname, 'NONE', None, 'Toggle Inputs', False, (('sockets_to_hide', 'INPUT'),)),
    (NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS.bl_idname, 'NONE', None, 'Toggle Outputs', False, (('sockets_to_hide', 'OUTPUT'),)),
    (NODEUTILS_OT_SWITCH_VIEWER_DOMAIN.bl_idname, 'NONE', None, 'Switch to First', False, (('switch_mode', 'SWITCH_TO_FIRST'),)),
    (NODEUTILS_OT_SWITCH_VIEWER_DOMAIN.bl_idname, 'NONE', None, 'Switch to Last', False, (('switch_mode', 'SWITCH_TO_LAST'),)),
    (NODEUTILS_OT_SWITCH_VIEWER_DOMAIN.bl_idname, 'NONE', None, 'Cycle Up', False, (('switch_mode', 'CYCLE_UP'),)),
    (NODEUTILS_OT_SWITCH_VIEWER_DOMAIN.bl_idname, 'NONE', None, 'Cycle Down', False, (('switch_mode', 'CYCLE_DOWN'),)),
    (NODEUTILS_OT_SWITCH_VIEWER_DOMAIN_INVOKE_MENU.bl_idname, 'NONE', None, 'Invoke Pie Menu', False, None,),
    (NODEUTILS_OT_BATCH_LABEL.bl_idname, 'NONE', 'Batch Operations', 'Set Labels', False, None,),
    (NODEUTILS_OT_BATCH_LABEL.bl_idname, 'NONE', 'Batch Operations', 'Set Labels', False, None,),
    (NODEUTILS_OT_SET_WIDTH.bl_idname, 'NONE', 'Batch Operations', '', False, None,),
    (NODEUTILS_OT_SET_COLOR.bl_idname, 'NONE', 'Batch Operations', 'Set Color', False, (('color_opmode', 'SET_COLOR'),),),
    (NODEUTILS_OT_SET_COLOR.bl_idname, 'NONE', 'Batch Operations', 'Clear Color', False, (('color_opmode', 'CLEAR_COLOR'),),),
    (NODEUTILS_OT_RECENTER_NODES.bl_idname, 'NONE', 'Batch Operations', 'Center at Origin', False, None,),
)


def register():
    addon_keymaps.clear()
    if key_config := bpy.context.window_manager.keyconfigs.addon:
        for operator, key, category, label, is_repeat, props in reversed(keymap_defs):
            key_map = key_config.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
            key_entry = key_map.keymap_items.new(operator, key, repeat=is_repeat, value='PRESS')
            if props:
                for prop, value in props:
                    setattr(key_entry.properties, prop, value)

            addon_keymaps.append((key_map, key_entry, label))
            category_entry = prefs_display.get(key_entry.name, category)
            prefs_display[key_entry.name] = category_entry

def unregister():
    for key_map, key_entry, label in addon_keymaps:
        key_map.keymap_items.remove(key_entry)
    addon_keymaps.clear()
    
