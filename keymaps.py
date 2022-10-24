import bpy
from .operators import (
    NODEUTILS_OT_SELECT_BY_TYPE,
    NODEUTILS_OT_NORMALIZE_NODE_WIDTH,
    NODEUTILS_OT_BATCH_LABEL,
    NODEUTILS_OT_SET_WIDTH,
    NODEUTILS_OT_LABEL_REROUTES,
    NODEUTILS_OT_RECENTER_NODES,
    NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS,
    
)

addon_keymaps = []
keymap_defs = (
    (NODEUTILS_OT_SELECT_BY_TYPE.bl_idname, 'NONE', (('select_target', 'NODES'),)),
    (NODEUTILS_OT_SELECT_BY_TYPE.bl_idname, 'NONE', (('select_target', 'REROUTES'),)),
    (NODEUTILS_OT_SELECT_BY_TYPE.bl_idname, 'NONE', (('select_target', 'FRAMES'),)),
    (NODEUTILS_OT_NORMALIZE_NODE_WIDTH.bl_idname, 'NONE',(('normalize_type', 'MAX'),)),
    (NODEUTILS_OT_NORMALIZE_NODE_WIDTH.bl_idname, 'NONE',(('normalize_type', 'MIN'),)),
    (NODEUTILS_OT_NORMALIZE_NODE_WIDTH.bl_idname, 'NONE',(('normalize_type', 'AVERAGE'),)),
    (NODEUTILS_OT_BATCH_LABEL.bl_idname, 'NONE', None),
    (NODEUTILS_OT_SET_WIDTH.bl_idname, 'NONE', None),
    (NODEUTILS_OT_LABEL_REROUTES.bl_idname, 'NONE',(('check_by', 'INPUT'),)),
    (NODEUTILS_OT_LABEL_REROUTES.bl_idname, 'NONE',(('check_by', 'OUTPUT'),)),
    (NODEUTILS_OT_RECENTER_NODES.bl_idname, 'NONE', None),
    (NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS.bl_idname, 'NONE',(('sockets_to_hide', 'INPUT'),)),
    (NODEUTILS_OT_TOGGLE_UNUSED_SOCKETS.bl_idname, 'NONE',(('sockets_to_hide', 'OUTPUT'),)),
)


def register():
    addon_keymaps.clear()
    if key_config := bpy.context.window_manager.keyconfigs.addon:
        for operator, key, props in reversed(keymap_defs):
            key_map = key_config.keymaps.new(name='Node Editor', space_type="NODE_EDITOR")
            key_entry = key_map.keymap_items.new(operator, key, value='PRESS')
            if props:
                for prop, value in props:
                    setattr(key_entry.properties, prop, value)


            addon_keymaps.append((key_map, key_entry))

def unregister():
    for key_map, key_entry in addon_keymaps:
        key_map.keymap_items.remove(key_entry)
    addon_keymaps.clear()
    
