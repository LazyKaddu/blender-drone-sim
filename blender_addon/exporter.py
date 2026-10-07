import bpy
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os

def export_scene_to_urdf(filepath):
    """
    Parses the current Blender scene, generates a valid URDF XML string 
    representing all static obstacles, and writes it to disk.
    It exports actual meshes (.obj) and textures for accurate geometry.
    """
    urdf_dir = os.path.dirname(filepath)
    os.makedirs(urdf_dir, exist_ok=True)
    
    assets_dir = os.path.join(urdf_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    
    robot = ET.Element("robot", name="blender_world")
    
    # In PyBullet, a single URDF must have all links connected via joints to a root link.
    # We create a dummy root link called 'world_base'.
    ET.SubElement(robot, "link", name="world_base")
    
    # Save current selection state so we don't annoy the user
    active_obj = bpy.context.view_layer.objects.active
    selected_objects = bpy.context.selected_objects.copy()
    
    for obj in bpy.context.scene.objects:
        # We only export meshes, and we ignore the Drone itself!
        if obj.type == 'MESH' and not obj.name.lower().startswith("drone"):
            
            link_name = f"link_{obj.name.replace('.', '_')}"
            link = ET.SubElement(robot, "link", name=link_name)
            
            # Inertial (mass=0 makes it a static, immovable obstacle in PyBullet)
            inertial = ET.SubElement(link, "inertial")
            ET.SubElement(inertial, "mass", value="0.0")
            ET.SubElement(inertial, "origin", xyz="0 0 0", rpy="0 0 0")
            ET.SubElement(inertial, "inertia", ixx="0", ixy="0", ixz="0", iyy="0", iyz="0", izz="0")
            
            # Select only this object to export it
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            
            obj_filename = f"{obj.name.replace('.', '_')}.obj"
            obj_filepath = os.path.join(assets_dir, obj_filename)
            
            # Export the mesh to OBJ with materials
            try:
                # Blender 3.2+ / 4.x
                bpy.ops.wm.obj_export(
                    filepath=obj_filepath, 
                    export_selected_objects=True,
                    forward_axis='Y',
                    up_axis='Z',
                    export_materials=True
                )
            except AttributeError:
                # Fallback for older Blender versions
                bpy.ops.export_scene.obj(
                    filepath=obj_filepath, 
                    use_selection=True,
                    axis_forward='Y',
                    axis_up='Z',
                    use_materials=True
                )
            
            # Visual Geometry
            visual = ET.SubElement(link, "visual")
            ET.SubElement(visual, "origin", xyz="0 0 0", rpy="0 0 0") 
            geom = ET.SubElement(visual, "geometry")
            ET.SubElement(geom, "mesh", filename=f"assets/{obj_filename}")
            
            # Collision Geometry
            collision = ET.SubElement(link, "collision")
            ET.SubElement(collision, "origin", xyz="0 0 0", rpy="0 0 0")
            geom_coll = ET.SubElement(collision, "geometry")
            ET.SubElement(geom_coll, "mesh", filename=f"assets/{obj_filename}")
            
            # Finally, connect this obstacle to the 'world_base'
            joint_name = f"joint_{obj.name.replace('.', '_')}"
            joint = ET.SubElement(robot, "joint", name=joint_name, type="fixed")
            ET.SubElement(joint, "parent", link="world_base")
            ET.SubElement(joint, "child", link=link_name)
            
            # Since the OBJ exporter naturally bakes the world transforms into the mesh,
            # we must place the joint exactly at the origin to prevent double-transforms.
            ET.SubElement(joint, "origin", xyz="0 0 0", rpy="0 0 0")
            
    # Restore original selection state
    bpy.ops.object.select_all(action='DESELECT')
    for obj in selected_objects:
        obj.select_set(True)
    if active_obj:
        bpy.context.view_layer.objects.active = active_obj
            
    # Pretty-print the XML
    xml_string = ET.tostring(robot, encoding="utf-8")
    parsed_xml = xml.dom.minidom.parseString(xml_string)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    
    # Save to disk
    with open(filepath, "w") as f:
        f.write(pretty_xml)
        
    print(f"[Drone Sim] Exported URDF successfully to: {filepath}")
