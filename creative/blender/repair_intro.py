"""Rebuild the Revive studio animation with Blender 4.5 LTS."""
import bpy, math, os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out=os.path.join(root,'static','motion','v2');os.makedirs(out,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def material(name,color,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=.28
 return m
def box(name,location,scale,mat,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(size=1,location=location);o=bpy.context.object;o.name=name;o.dimensions=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 mod=o.modifiers.new('Soft precision edges','BEVEL');mod.width=bevel;mod.segments=5;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o
teal=material('Deep teal',(.008,.018,.045));metal=material('Titanium',(.25,.31,.32),.8);glass=material('Screen glass',(.015,.09,.2),.3);gold=material('Warm brass',(.02,.45,.8),.7)
bpy.ops.object.empty_add();rig=bpy.context.object;rig.name='Device turntable'
for o in [box('Phone frame',(0,0,1.6),(1.5,.16,2.8),metal),box('Screen',(0,-.1,1.6),(1.36,.035,2.6),glass),box('Speaker',(0,-.125,2.73),(.3,.02,.035),metal,.015)]:o.parent=rig
for z in [.95,1.35,1.75]:
 o=box('Screen accent',(-.22,-.125,z),(.7,.02,.055),gold,.02);o.parent=rig
# A separated display settles toward its frame, showing repair as precision craft.
display=bpy.data.objects.get('Screen')
for frame,y in [(1,-.65),(25,-.30),(49,-.10),(73,-.65)]:
 display.location.y=y;display.keyframe_insert(data_path='location',frame=frame)
# Luminous arcs provide depth without putting text inside the render.
for radius,z in [(2.0,.02),(2.25,-.01)]:
 bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=.015,location=(0,0,z))
 bpy.context.object.data.materials.append(gold)
box('Studio plinth',(0,0,.08),(3.8,2.4,.16),teal)
box('Studio floor',(0,0,-.12),(200,200,.1),teal)
for frame,angle in [(1,-.45),(37,.35),(73,-.45)]:rig.rotation_euler[2]=angle;rig.keyframe_insert(data_path='rotation_euler',frame=frame)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
for loc,power,color,size in [((-3,-4,6),900,(.7,.85,1),5),((4,1,4),1100,(.1,.6,1),3),((0,4,6),1200,(1,1,1),4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.color=color;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1))
bpy.ops.object.camera_add(location=(4,-8,4.2));cam=bpy.context.object;aim(cam,(0,0,1.5));cam.data.type='ORTHO';cam.data.ortho_scale=5.8
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=True;s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.fps=12;s.frame_end=72
s.world.color=(.08,.08,.08);s.render.image_settings.file_format='PNG';s.render.filepath=os.path.join(out,'repair-poster.png');s.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'creative','blender','repair-intro-v2.blend'))
bpy.ops.render.render(write_still=True)
s.render.image_settings.file_format='FFMPEG';s.render.ffmpeg.format='MPEG4';s.render.ffmpeg.codec='H264';s.render.ffmpeg.constant_rate_factor='MEDIUM';s.render.filepath=os.path.join(out,'repair-intro.mp4');bpy.ops.render.render(animation=True)

with open(os.path.join(out,'ready.txt'),'w') as f: f.write('Rendered successfully with Blender 4.5 LTS\n')
