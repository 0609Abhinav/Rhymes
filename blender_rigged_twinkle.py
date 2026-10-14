"""Build a locally-rendered, fully articulated cartoon sing-along in Blender.

Run with Blender's bundled Python:
  blender.exe --background --python blender_rigged_twinkle.py -- --preview
The full render writes a transparent character pass, then composites it over
the inpainted illustrated backgrounds and the existing sung soundtrack.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

ROOT = os.path.dirname(os.path.abspath(__file__))
WIDTH, HEIGHT, FPS, SECONDS = 1280, 720, 24, 80
TOTAL = FPS * SECONDS
FRAME_DIR = os.path.join(ROOT, "rigged_frames")
BACKGROUND_DIR = os.path.join(ROOT, "rigged_backgrounds")
OUT_DIR = os.path.join(ROOT, "blender_character_pass")
os.makedirs(OUT_DIR, exist_ok=True)

def material(name, color, roughness=.56, emission=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = roughness
    if emission:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emission
    return m

CREAM = material("warm cream plush", (.92, .77, .59))
WHITE = material("soft ivory", (1.0, .91, .78))
BLUE = material("starry blue pajamas", (.16, .48, .82))
PINK = material("ear and tongue pink", (.94, .29, .37))
DARK = material("deep cocoa eyes and mouth", (.105, .038, .038), .26)
HILITE = material("eye highlights", (1, 1, 1), .12, .2)
BLUSH = material("soft rosy cheeks", (1, .38, .42), .66)
ORANGE = material("fox orange", (.88, .30, .075))
GOLD = material("warm star gold", (1.0, .62, .055), .32, .35)
SUN = material("sunshine", (1.0, .48, .08), .3, .25)

def smooth(obj):
    if obj.type == "MESH":
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj

def uv(name, loc, size, mat, parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, radius=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(mat)
    smooth(o)
    if parent:
        o.parent = parent
    return o

def empty(name, loc, parent=None):
    o = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(o)
    o.location = loc
    if parent:
        o.parent = parent
    return o

def set_visible(obj, start, end):
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=1)
    obj.hide_render = False
    obj.keyframe_insert(data_path="hide_render", frame=start)
    obj.keyframe_insert(data_path="hide_render", frame=end)
    obj.hide_render = True
    obj.keyframe_insert(data_path="hide_render", frame=min(TOTAL, end + 1))

def key(obj, path, frame, value):
    setattr(obj, path, value)
    obj.keyframe_insert(data_path=path, frame=frame)

def add_background_plane(path, index):
    mesh = bpy.data.meshes.new(f"illustration-{index}")
    verts = [(-3.2, 0, -1.856), (3.2, 0, -1.856), (3.2, 0, 1.856), (-3.2, 0, 1.856)]
    mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
    obj = bpy.data.objects.new(f"background-{index}", mesh)
    bpy.context.collection.objects.link(obj)
    m = bpy.data.materials.new(f"illustration material {index}")
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    tex = n.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path, check_existing=True)
    emit = n.new("ShaderNodeEmission")
    out = n.new("ShaderNodeOutputMaterial")
    m.node_tree.links.new(tex.outputs["Color"], emit.inputs["Color"])
    m.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    obj.data.materials.append(m)
    obj.location = (0, 2.2, 1.8)
    set_visible(obj, 1 + (index-1)*FPS*8, min(TOTAL, index*FPS*8))
    return obj

def make_bunny(kind="bunny"):
    root = empty(kind + " rig root", (0, 0, 0))
    isfox = kind == "fox"
    fur = ORANGE if isfox else CREAM
    tummy = WHITE
    body = uv(kind+" torso", (0, 0, 1.05), (.60, .43, .88), fur, root)
    uv(kind+" tummy", (0, -.405, 1.12), (.39, .09, .55), tummy, root)
    # Clothing accent that reads clearly against the detailed story art.
    if not isfox:
        uv(kind+" blue front", (0, -.476, 1.14), (.31, .045, .42), BLUE, root)
        for z in (1.00, 1.19, 1.37):
            uv(kind+" pajama star", (0, -.526, z), (.038, .012, .038), GOLD, root)

    head = empty(kind+" head turn", (0, 0, 1.93), root)
    uv(kind+" head", (0, 0, .43), (.77, .62, .70), fur, head)
    # Ears are individually hinged and can flop and point as the character moves.
    ears = []
    for side, label in ((-1, "L"), (1, "R")):
        ear = empty(kind+" ear hinge "+label, (side*.36, 0, 1.02), head)
        ears.append(ear)
        if isfox:
            bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.30, radius2=.025, depth=.92, location=(0, 0, 0))
            outer = bpy.context.object
            outer.name = kind+" pointed ear "+label
            outer.scale = (1, .52, 1)
            outer.location = (side*.02, 0, .40)
            outer.data.materials.append(ORANGE)
            smooth(outer); outer.parent = ear
            inner = uv(kind+" inner ear "+label, (side*.02, -.17, .40), (.16, .035, .33), PINK, ear)
        else:
            outer = uv(kind+" floppy ear "+label, (side*.03, 0, .40), (.25, .16, .53), fur, ear)
            inner = uv(kind+" inner ear "+label, (side*.03, -.151, .40), (.15, .035, .36), PINK, ear)

    # Muzzle, cheeks, nose, eyes and separate animated mouth.
    for side, label in ((-1, "L"), (1, "R")):
        uv(kind+" muzzle "+label, (side*.135, -.555, .25), (.19, .105, .145), WHITE, head)
        uv(kind+" cheek "+label, (side*.49, -.476, .19), (.12, .035, .095), BLUSH, head)
        uv(kind+" eye "+label, (side*.285, -.559, .56), (.112, .07, .145), DARK, head)
        uv(kind+" eye sparkle "+label, (side*.311, -.62, .615), (.031, .018, .039), HILITE, head)
        brow = uv(kind+" brow "+label, (side*.29, -.55, .77), (.105, .027, .025), CREAM if not isfox else SUN, head)
        brow.rotation_euler[1] = side * -.14
    uv(kind+" nose", (0, -.662, .29), (.08, .052, .055), PINK, head)
    mouth = uv(kind+" singing mouth", (0, -.637, .095), (.16, .035, .12), DARK, head)
    tongue = uv(kind+" mouth tongue", (0, -.672, .045), (.085, .02, .032), PINK, head)
    # Start with an almost-closed smile. Mouth scale is keyed to vocal energy below.
    mouth.scale.z = .025
    tongue.scale.z = .001

    # Arms have shoulder pivots; wrists and hands are independent pieces.
    arms = []
    for side, label in ((-1, "L"), (1, "R")):
        shoulder = empty(kind+" shoulder "+label, (side*.48, 0, 1.62), root)
        sleeve = BLUE if not isfox else ORANGE
        uv(kind+" arm "+label, (side*.19, -.015, -.22), (.22, .20, .39), sleeve, shoulder)
        uv(kind+" paw "+label, (side*.32, -.065, -.48), (.17, .15, .17), WHITE, shoulder)
        arms.append(shoulder)

    legs = []
    for side, label in ((-1, "L"), (1, "R")):
        hip = empty(kind+" hip "+label, (side*.25, 0, .48), root)
        uv(kind+" leg "+label, (0, 0, -.20), (.23, .25, .36), fur, hip)
        uv(kind+" foot "+label, (0, -.22, -.43), (.29, .40, .16), WHITE if not isfox else fur, hip)
        legs.append(hip)

    tail = uv(kind+" fluffy tail", (-.04, .40, .60), (.35, .32, .33), WHITE if not isfox else ORANGE, root)
    if isfox:
        uv(kind+" tail tip", (-.04, .65, .60), (.23, .19, .23), WHITE, root)
    # Soft blue night pajamas with star glints on the lower torso.
    return {"root": root, "head": head, "ears": ears, "arms": arms, "legs": legs,
            "mouth": mouth, "tongue": tongue, "tail": tail, "isfox": isfox}

def make_star():
    root = empty("singing star rig", (0, 0, 0))
    outline=[]
    for i in range(10):
        a=math.pi/2 + i*math.pi/5
        r=1.0 if i%2==0 else .48
        outline.append((math.cos(a)*r, math.sin(a)*r))
    # A beveled extruded five-point star, facing camera along -Y.
    verts=[(x, y, z) for y in (-.12,.12) for x,z in outline]
    faces=[tuple(range(9,-1,-1)),tuple(range(10,20))]
    for i in range(10): faces.append((i,(i+1)%10,(i+1)%10+10,i+10))
    mesh=bpy.data.meshes.new("five point rounded star mesh")
    mesh.from_pydata(verts,[],faces);mesh.materials.append(GOLD)
    obj=bpy.data.objects.new("gold star body",mesh);bpy.context.collection.objects.link(obj);obj.parent=root
    bevel=obj.modifiers.new("soft rounded points","BEVEL");bevel.width=.09;bevel.segments=3
    obj.modifiers.new("weighted corner normals","WEIGHTED_NORMAL")
    for side,label in ((-1,"L"),(1,"R")):
        uv("star eye "+label,(side*.30,-.17,.20),(.10,.055,.13),DARK,root)
        uv("star eye shine "+label,(side*.32,-.218,.25),(.025,.014,.03),HILITE,root)
        uv("star cheek "+label,(side*.52,-.17,-.04),(.10,.025,.06),BLUSH,root)
    mouth=uv("star singing mouth",(0,-.18,-.13),(.14,.04,.11),DARK,root)
    mouth.scale.z=.025
    return {"root":root,"head":root,"ears":[],"arms":[],"legs":[],"mouth":mouth,"tongue":None,"tail":None}

def animate_actor(actor, scene_idx, center_x, base_z, size, frame0, audio_env):
    root=actor["root"]
    start=frame0+1; end=min(TOTAL,frame0+FPS*8)
    set_visible(root,start,end)
    # Hide/show the whole articulated hierarchy by keying the rig root scale.
    root.location=(center_x,0,base_z)
    root.scale=(0,0,0); root.keyframe_insert("scale",frame=max(1,start-1))
    root.scale=(size,size,size); root.keyframe_insert("scale",frame=start)
    root.keyframe_insert("scale",frame=end)
    if end<TOTAL:
        root.scale=(0,0,0); root.keyframe_insert("scale",frame=end+1)
    # Action beats vary by verse: look, wave, stretch, dance, walk, cuddle, yawn, finale.
    period=FPS*2
    for f in range(start,end+1,6):
        sec=(f-start)/FPS
        ph=sec*2*math.pi/2.0
        if scene_idx in (3,8,9):
            bounce=.10*(.5+.5*math.sin(ph*2))
            sway=.13*math.sin(ph)
            left=1.05*math.sin(ph)
            right=-1.05*math.sin(ph+math.pi*.72)
            leg_l=.38*math.sin(ph+math.pi)
            leg_r=.38*math.sin(ph)
        elif scene_idx in (1,2):
            bounce=.06*(.5+.5*math.sin(ph))
            sway=.04*math.sin(ph)
            left=.15+.95*(.5+.5*math.sin(ph))
            right=-.08
            leg_l=.12*math.sin(ph);leg_r=-leg_l
        elif scene_idx in (4,5):
            bounce=.07*(.5+.5*math.sin(ph*2))
            sway=.09*math.sin(ph)
            left=.48*math.sin(ph);right=-.48*math.sin(ph)
            leg_l=.44*math.sin(ph);leg_r=-leg_l
        else:
            bounce=.035*(.5+.5*math.sin(ph))
            sway=.035*math.sin(ph)
            left=.25+.24*math.sin(ph)
            right=-.22+.2*math.sin(ph+1.4)
            leg_l=.1*math.sin(ph);leg_r=.1*math.sin(ph+math.pi)
        root.location.z=base_z+bounce
        root.keyframe_insert("location",frame=f)
        root.rotation_euler[1]=sway
        root.keyframe_insert("rotation_euler",frame=f)
        actor["head"].rotation_euler[1]=.08*math.sin(ph+.5)
        actor["head"].rotation_euler[2]=.09*math.sin(ph*.5)
        actor["head"].keyframe_insert("rotation_euler",frame=f)
        for j,e in enumerate(actor["ears"]):
            e.rotation_euler[1]=.18*math.sin(ph*1.3+j*1.2)
            e.keyframe_insert("rotation_euler",frame=f)
        for j,a in enumerate(actor["arms"]):
            a.rotation_euler[1]=(left if j==0 else right)
            a.keyframe_insert("rotation_euler",frame=f)
        for j,leg in enumerate(actor["legs"]):
            leg.rotation_euler[1]=(leg_l if j==0 else leg_r)
            leg.keyframe_insert("rotation_euler",frame=f)
        if actor.get("tail"):
            actor["tail"].rotation_euler[1]=.16*math.sin(ph*1.5)
            actor["tail"].keyframe_insert("rotation_euler",frame=f)
    # Key a small, lyric-energy-driven mouth opening and tongue reveal every frame.
    if actor["mouth"]:
        for f in range(start,end+1):
            level=float(audio_env[min(f-1,len(audio_env)-1)])
            opening=max(.025, min(.23, .025 + level*.18))
            actor["mouth"].scale.z=opening
            actor["mouth"].keyframe_insert("scale",frame=f)
            if actor.get("tongue"):
                actor["tongue"].scale.z=.035 if level>.56 else .001
                actor["tongue"].keyframe_insert("scale",frame=f)

def read_audio_envelope():
    import wave
    import numpy as np
    p=os.path.join(ROOT,"singing_vocals.wav")
    with wave.open(p,"rb") as w:
        rate=w.getframerate();raw=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)
    step=max(1,int(rate/FPS));env=[]
    for i in range(0,len(raw),step):
        chunk=raw[i:i+step]
        env.append(float(np.sqrt(np.mean(chunk*chunk))))
    env=np.asarray(env,dtype=np.float32)
    env=np.clip(env/max(float(np.percentile(env,95)),1),0,1)
    # smooth RMS over roughly 80 ms, preserving consonant pauses
    return np.convolve(env,np.ones(3,dtype=np.float32)/3,mode="same").tolist()

def main():
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes,bpy.data.curves,bpy.data.materials,bpy.data.cameras,bpy.data.lights,bpy.data.images):
        for d in list(datablocks):
            if d.users==0: datablocks.remove(d)
    sc=bpy.context.scene
    sc.render.engine="BLENDER_EEVEE_NEXT"
    sc.render.resolution_x=WIDTH;sc.render.resolution_y=HEIGHT;sc.render.resolution_percentage=100
    sc.render.fps=FPS;sc.render.film_transparent=True
    sc.view_settings.view_transform="Standard"
    sc.render.image_settings.file_format="PNG";sc.render.image_settings.color_mode="RGBA"
    sc.eevee.taa_render_samples=8
    camera_data=bpy.data.cameras.new("story camera");camera=bpy.data.objects.new("story camera",camera_data);sc.collection.objects.link(camera)
    camera.location=(0,-12,1.8);camera.rotation_euler=(math.pi/2,0,0);camera_data.type="ORTHO";camera_data.ortho_scale=6.6;sc.camera=camera
    # Use gentle front lighting with EEVEE's soft shadows where available.
    light_data=bpy.data.lights.new("large softbox","AREA");light=bpy.data.objects.new("large softbox",light_data);sc.collection.objects.link(light)
    light.location=(-3,-5,6);light_data.energy=650;light_data.size=5
    sc.world.color=(.6,.6,.6)

    bgfiles=[os.path.join(BACKGROUND_DIR,f"scene_{i:02d}.png") for i in range(1,11)]
    for i,p in enumerate(bgfiles,1):
        if os.path.isfile(p): add_background_plane(p,i)
    bunny=make_bunny("bunny");fox=make_bunny("fox");star=make_star()
    # Place and activate characters according to the existing story board.
    boxes={
      0:((380,145,770,715),(850,95,970,235)),1:((235,55,650,525),(785,120,990,370)),
      2:((700,55,1005,715),(185,205,545,565)),3:((300,245,695,710),(635,70,865,335)),
      4:((470,240,855,715),(760,55,965,285)),5:((490,235,865,715),(755,45,965,285)),
      6:((195,250,660,710),(770,135,1010,420)),7:(None,(455,65,820,505)),
      8:((635,215,1005,715),(510,45,820,325)),9:((175,250,565,715),(545,365,835,690))}
    env=read_audio_envelope()
    # Bunny/fox actor is repositioned on each verse and animated with gestures.
    for idx,(mammal,other) in boxes.items():
        frame0=idx*FPS*8
        if mammal:
            if idx in (4,5): actor=fox
            else: actor=bunny
            x1,y1,x2,y2=mammal
            cx=(x1+x2)/2; bottom=y2
            wx=(cx-WIDTH/2)/WIDTH*6.6
            wz=1.8+(HEIGHT/2-bottom)/HEIGHT*(6.6*HEIGHT/WIDTH)
            size=.84 if idx not in (1,6,9) else .76
            animate_actor(actor,idx,wx,wz,size,frame0,env)
        # A 3D star character takes over from the removed illustrated star.
        x1,y1,x2,y2=other;cx=(x1+x2)/2;cy=(y1+y2)/2
        wx=(cx-WIDTH/2)/WIDTH*6.6
        wz=1.8+(HEIGHT/2-cy)/HEIGHT*(6.6*HEIGHT/WIDTH)
        size=max(.24,min(.62,(x2-x1)/WIDTH*6.6*.5))
        star["root"].location=(wx,0,wz)
        set_visible(star["root"],frame0+1,min(TOTAL,frame0+FPS*8))
        first=frame0+1;last=min(TOTAL,frame0+FPS*8)
        star["root"].scale=(0,0,0);star["root"].keyframe_insert("scale",frame=max(1,first-1))
        star["root"].scale=(size,size,size);star["root"].keyframe_insert("scale",frame=first)
        star["root"].keyframe_insert("scale",frame=last)
        if last<TOTAL:
            star["root"].scale=(0,0,0);star["root"].keyframe_insert("scale",frame=last+1)
        for f in range(frame0+1,min(TOTAL,frame0+FPS*8)+1,6):
            t=(f-frame0)/FPS
            star["root"].location.z=wz+.08*math.sin(t*2.3+idx)
            star["root"].rotation_euler[1]=.07*math.sin(t*1.5)
            star["root"].keyframe_insert("location",frame=f);star["root"].keyframe_insert("rotation_euler",frame=f)
        for f in range(frame0+1,min(TOTAL,frame0+FPS*8)+1):
            level=env[min(f-1,len(env)-1)]
            star["mouth"].scale.z=max(.02,min(.22,.02+level*.16))
            star["mouth"].keyframe_insert("scale",frame=f)

    # Use linear interpolation for audio visemes; smooth motion controls stay Bezier.
    for act in bpy.data.actions:
        for fc in act.fcurves:
            if "singing mouth" in act.name:
                for kp in fc.keyframe_points: kp.interpolation="LINEAR"
    sc.frame_start=1;sc.frame_end=TOTAL;sc.frame_set(1)
    sc.render.filepath=os.path.join(OUT_DIR,"frame_")
    blend_path=os.path.join(ROOT,"Twinkle_Rigged_Animation.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    preview="--preview" in sys.argv
    if preview:
        sc.render.resolution_percentage=50
        sc.render.filepath=os.path.join(ROOT,"rigged_preview.png")
        sc.frame_set(90);bpy.ops.render.render(write_still=True)
    else:
        sc.render.image_settings.file_format="PNG"
        sc.render.resolution_percentage=100
        bpy.ops.render.render(animation=True)

if __name__=="__main__": main()
