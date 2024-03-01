bl_info = {
    "name": "Bake Render Textures",
    "author": "Mikhail Lebedev",
    "version": (1, 0, 0),
    "blender": (3, 6, 5),
    "location": "NODE_EDITOR > Side Panel",
    "description": "Bake Animated Texture",
    "category": "Animation",
}

import bpy

def texture_node(self, context):
    # Get the active node's image name
    active_node = bpy.context.active_node
    
    return active_node.image.name if active_node else ""

class BakeSettings(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", description="render folder path")
    texture_node: bpy.props.StringProperty(default = texture_node,name = "Image Texture Node", description = "Select any Texture Node")

class BakeAnimationOperator(bpy.types.Operator):
    bl_idname = "bake.anim_texture_bake"
    bl_label = "Bake Textures Operator"
    bl_description = "Bake Texture on every frame and save in the folder"
    '''
    #This class is for Modal Operator Bake that will
    #run the blender bake operator in sequence one after another
    #and save the image with frame number bake_####.png
    '''
    
    pass
    
class BakeAnimationPanel(bpy.types.Panel):
    bl_space_type = 'NODE_EDITOR'
    bl_label = "Bake Textures Panel"
    bl_region_type = "UI"
    bl_category = "Bake Textures"
    
    '''
    #This class is for visualizing the panel
    #that will be visible when the image texture node
    #is selected in the node editor side panel
    #bake animation tab  will be visible
    #in the panel will be a url to the folder
    #where it will save all the baked images
    #update frame button is for baking current frame
    #and saving it over existing image file
    '''
    @classmethod
    def poll(cls, context):
        space = context.space_data
        node = context.active_node
        image = getattr(node, 'image', None)
        return image and space.type == 'NODE_EDITOR'

    def draw(self, context):
        data = bpy.data.materials[context.space_data.id.name].node_tree
        active_node = context.active_node
        
        
        layout = self.layout
        col = layout.column()
        col.prop(context.scene.anim_bake_settings, "filepath", text="")
        
        row = col.row()
        row.label(text="image:")
        row.prop(context.scene.anim_bake_settings, "texture_node", text="")
        
        
        col2 = layout.column()
        col2.operator(BakeAnimationOperator.bl_idname, icon="RENDER_ANIMATION", text="render")
        
        
    

classes = (
            BakeAnimationPanel,
            BakeAnimationOperator,
            BakeSettings,
        )
        
def register():
    for my_class in classes:
        bpy.utils.register_class(my_class)
    #properties
    bpy.types.Scene.anim_bake_settings = bpy.props.PointerProperty(type=BakeSettings)
        
def unregister():
    for my_class in classes:
        bpy.utils.unregister_class(my_class)
            
if __name__ == '__main__':
    register()