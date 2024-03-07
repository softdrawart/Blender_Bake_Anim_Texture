bl_info = {
    "name": "Bake Bake Textures",
    "author": "Mikhail Lebedev",
    "version": (1, 0, 0),
    "blender": (3, 6, 5),
    "location": "NODE_EDITOR > Side Panel",
    "description": "Bake Animated Texture",
    "category": "Animation",
}

import bpy, shutil, os

def texture_node(self, context):
    # Get the active node's image name
    active_node = bpy.context.active_node
    
    return active_node.image.name if active_node else ""

class BakeSettings(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", description="bake folder path")
    hide_hair: bpy.props.BoolProperty(name="hide hair", description="hide hair before baking", default=True)
    #texture_node: bpy.props.StringProperty(name = "Image Texture Node", description = "Select any Texture Node")

class BakeAnimationOperator(bpy.types.Operator):
    bl_idname = "bake.anim_texture_bake"
    bl_label = "Bake Textures Operator"
    bl_description = "Bake Texture on every frame and save in the folder"
    '''
    #This class is for Modal Operator Bake that will
    #run the blender bake operator in sequence one after another
    #and save the image with frame number bake_####.png
    '''
    baking = False
    _cancel = False
    _timer = None
    bake_frame: bpy.props.BoolProperty(default=False)  # frame bakeing
    img: bpy.props.StringProperty(default='') # image bakeed
    hair_modfier_list = [] #disabled hair modifier list
    def hide_hair_list(self, object_name):
        hair_modifiers = []
        
        # Get the object by name
        obj = bpy.data.objects.get(object_name)
        if obj is None:
            return hair_modifiers  # Return an empty list if the object is not found
        
        # Loop through all modifiers of the object
        for modifier in obj.modifiers:
            if modifier.type == 'PARTICLE_SYSTEM':
                particle_system = modifier.particle_system
                if particle_system.settings.type == 'HAIR' and modifier.show_render:
                    # Append the hair type modifier to the list
                    hair_modifiers.append(modifier.name)
                    # Turn off render visibility mode
                    modifier.show_render = False
        
        return hair_modifiers
        
    def enable_hair(self):
        obj = bpy.context.active_object
        # Loop through all modifiers of the object
        if obj:
            for modifier_name in self.hair_modfier_list:
                if modifier_name in obj.modifiers:
                    # Turn on render visibility mode
                    obj.modifiers[modifier_name].show_render = True
        return obj
    def get_or_create_and_activate_image_node(self, material_name, image_name):
        # Find the material
        material = bpy.data.materials.get(material_name)
        if material is None:
            return None  # Material not found

        # Check if the material has a node tree
        if not material.use_nodes:
            material.use_nodes = True

        # Iterate through the nodes in the material's node tree
        for node in material.node_tree.nodes:
            if node.type == 'TEX_IMAGE' and node.image and node.image.name == image_name:
                material.node_tree.nodes.active = node  # Make the node active
                return node

        # If the image node doesn't exist, create a new one
        image_node = material.node_tree.nodes.new(type='ShaderNodeTexImage')
        image = bpy.data.images.get(image_name)
        if not image:
            return None  # Image not found
        image_node.image = image

        # Make the new image node active
        material.node_tree.nodes.active = image_node

        return image_node
    def filepath(self, img_name, location, frame):
        #set location to location set by user and a file name "filename####.png"
        #if no location set, set basename location to the bake image location
        if not location:
            location = os.path.dirname(bpy.data.images['testBack'].filepath) #set base location of the image
        else:
            abs_path = bpy.path.abspath(location)
            file_name = os.path.basename(abs_path)#get new file name set by user
            if file_name:
                img_name = file_name
                location = os.path.dirname(abs_path) + '\\' #get new dir path set by user
                print(f"location is {location}")
        path = bpy.path.abspath(f"{location}{img_name}{frame:04d}.png")
        return path
        
    def bake_complete(self, scene, context=None):
        print("Bake complete")
        
        #save image
        img = bpy.data.images[self.img] #get image data block
        print(f"Saving base image {img.filepath}")
        img.save()
        img_filepath_abs = bpy.path.abspath(img.filepath) #convert relative path of the original image to absolute
        
        filename = self.filepath(self.img, bpy.context.scene.anim_bake_settings.filepath, bpy.context.scene.frame_current) #form a new file name location
        print(f"Saving file {filename}")
        shutil.copyfile(img_filepath_abs, filename)#copy base image to new file location
        
        self.baking = False
        if not self.bake_frame:
            bpy.context.scene.frame_current += 1
    def bake_pre(self, scene, context=None):
        print("Bake started")
        self.baking = True
    def bake_cancel(self, scene, context=None):
        print("Bake cancelled")
        self._cancel = True
        self.bake = False
    @classmethod
    def poll(cls, context):
        return bpy.context.mode == 'OBJECT'
    def execute(self, context):
        #form hair modifier list
        if context.scene.anim_bake_settings.hide_hair:
            self.hair_modfier_list = self.hide_hair_list(context.active_object.name)
        #check if image is unpacked
        if bpy.data.images[self.img].packed_file:
            bpy.ops.image.unpack(id=self.img)
            print(f"unpacking image {self.img} to {bpy.data.images[self.img].filepath}")
        #set active image node for all materials, add node if it does not exist
        for mat in context.active_object.material_slots:
            self.get_or_create_and_activate_image_node(mat.name, self.img)
        #set local variable
        self.baking = False
        self._cancel = False
        #set frame start as our current frame
        if not self.bake_frame:
            context.scene.frame_current = context.scene.frame_start
        wm = bpy.context.window_manager
        #add bake handlers
        bpy.app.handlers.object_bake_complete.append(self.bake_complete)
        bpy.app.handlers.object_bake_cancel.append(self.bake_cancel)
        bpy.app.handlers.object_bake_pre.append(self.bake_pre)
        #call bake before going into modal check
        bpy.ops.object.bake('INVOKE_DEFAULT')
        #add timer
        self._timer = wm.event_timer_add(time_step = 0.5, window = context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    def modal(self, context, event):
        if event.type == 'TIMER':
            #if its not the end of the frame range and not single frame bake and the baking is finished then call another bake
            if context.scene.frame_current > context.scene.frame_end or self._cancel or (self.bake_frame and not self.baking):
                bpy.app.handlers.object_bake_complete.remove(self.bake_complete)
                bpy.app.handlers.object_bake_cancel.remove(self.bake_cancel)
                bpy.app.handlers.object_bake_pre.remove(self.bake_pre)
                #turn on previously turned off hair
                if context.scene.anim_bake_settings.hide_hair:
                    self.enable_hair()
                #remove timer
                context.window_manager.event_timer_remove(self._timer)
                if self._cancel:
                    return {'CANCELLED'}
                return {'FINISHED'}
            elif not self.baking:
                bpy.ops.object.bake('INVOKE_DEFAULT')
        elif event.type == 'ESC':
            bpy.app.handlers.object_bake_complete.remove(self.bake_complete)
            bpy.app.handlers.object_bake_cancel.remove(self.bake_cancel)
            bpy.app.handlers.object_bake_pre.remove(self.bake_pre)
            context.window_manager.event_timer_remove(self._timer)
            #turn on previously turned off hair
            if context.scene.anim_bake_settings.hide_hair:
                self.enable_hair()
            return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    
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
        return image and space.type == 'NODE_EDITOR' and space.tree_type == 'ShaderNodeTree'

    def draw(self, context):
        data = bpy.data.materials[context.space_data.id.name].node_tree
        active_node = context.active_node
        
        
        layout = self.layout
        col = layout.column()
        col.prop(context.scene.anim_bake_settings, "filepath", text="")
        
        row = col.row()
        row.label(text="image:")
        row.label(text=active_node.image.name)
        #row.prop(context.scene.anim_bake_settings, "texture_node", text="")
        
        
        col2 = layout.column()
        bake = col2.operator(BakeAnimationOperator.bl_idname, icon="RENDER_ANIMATION", text="bake full")
        bake.img = active_node.image.name
        bake.bake_frame = False
        
        bake_current = col2.operator(BakeAnimationOperator.bl_idname, icon="RENDER_STILL", text="bake current")
        bake_current.bake_frame = True
        bake_current.img = active_node.image.name
        
        hide_hair = col2.prop(context.scene.anim_bake_settings, "hide_hair", text="hide hair")
        
    

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
    #properties
    del bpy.types.Scene.anim_bake_settings
            
if __name__ == '__main__':
    register()