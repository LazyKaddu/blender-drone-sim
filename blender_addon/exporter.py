import bpy
import xml.etree.ElementTree as ET
import xml.dom.minidom
import os

def export_scene_to_urdf(filepath):
    """
    Parses the current Blender scene, generates a valid URDF XML string 
    representing all static obstacles, and writes it to disk.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    robot = ET.Element("robot", name="blender_world")
    
    # In PyBullet, a single URDF must have all links connected via joints to a root link.
    # We create a dummy root link called 'world_base'.
    ET.SubElement(robot, "link", name="world_base")
    
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
            
            # For this basic compiler, we use bounding box approximations 
            # based on the object's dimensions in Blender.
            dims = obj.dimensions
            
            # Visual Geometry
            visual = ET.SubElement(link, "visual")
            ET.SubElement(visual, "origin", xyz="0 0 0", rpy="0 0 0") 
            geom = ET.SubElement(visual, "geometry")
            ET.SubElement(geom, "box", size=f"{dims.x} {dims.y} {dims.z}")
            
            # Collision Geometry
            collision = ET.SubElement(link, "collision")
            ET.SubElement(collision, "origin", xyz="0 0 0", rpy="0 0 0")
            geom_coll = ET.SubElement(collision, "geometry")
            ET.SubElement(geom_coll, "box", size=f"{dims.x} {dims.y} {dims.z}")
            
            # Finally, connect this obstacle to the 'world_base' so PyBullet parses it as one structure
            joint_name = f"joint_{obj.name.replace('.', '_')}"
            joint = ET.SubElement(robot, "joint", name=joint_name, type="fixed")
            ET.SubElement(joint, "parent", link="world_base")
            ET.SubElement(joint, "child", link=link_name)
            
            # Extract transforms
            loc = f"{obj.location.x} {obj.location.y} {obj.location.z}"
            rot = f"{obj.rotation_euler.x} {obj.rotation_euler.y} {obj.rotation_euler.z}"
            ET.SubElement(joint, "origin", xyz=loc, rpy=rot)
            
    # Pretty-print the XML
    xml_string = ET.tostring(robot, encoding="utf-8")
    parsed_xml = xml.dom.minidom.parseString(xml_string)
    pretty_xml = parsed_xml.toprettyxml(indent="  ")
    
    # Save to disk
    with open(filepath, "w") as f:
        f.write(pretty_xml)
        
    print(f"[Drone Sim] Exported URDF successfully to: {filepath}")
