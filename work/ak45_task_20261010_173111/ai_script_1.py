import unreal
import os

# ---------- Helper Functions ----------
def log(msg):
    unreal.log(msg)

def raise_error(msg):
    raise Exception(msg)

# ---------- Step 1: Import AK45 Static Mesh ----------
def import_ak45():
    obj_path = r"C:\Users\asus\Desktop\UnrealAgent\work\ak45_task_20261010_173111\extracted\ak45.obj"
    if not os.path.isfile(obj_path):
        raise_error(f"AK45 OBJ file not found at {obj_path}")

    task = unreal.AssetImportTask()
    task.filename = obj_path
    task.destination_path = "/Game/Weapons"
    task.destination_name = "SM_AK45"
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.options = unreal.FbxImportUI()
    task.options.import_mesh = True
    task.options.import_as_skeletal = False
    task.options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    task.options.combine_meshes = False
    task.options.import_materials = True
    task.options.import_textures = True
    task.options.import_as_skeletal = False

    log(f"Importing AK45 static mesh from '{obj_path}' to '/Game/Weapons/SM_AK45'")
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    if not task.imported_object_paths:
        raise_error("Asset import task completed but no assets were created.")
    imported_path = task.imported_object_paths[0]
    static_mesh = unreal.EditorAssetLibrary.load_asset(imported_path)
    if not static_mesh:
        raise_error(f"Failed to load imported static mesh at {imported_path}")
    log(f"Successfully imported static mesh: {imported_path}")
    return static_mesh

# ---------- Step 2: Find Human Skeletal Mesh ----------
def find_human_skeletal_mesh():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    all_assets = registry.get_assets_by_path("/Game", recursive=True)
    skeletal_assets = [
        a for a in all_assets
        if a.asset_class == "SkeletalMesh" and not a.object_path.startswith("/Game/Weapons")
    ]

    if not skeletal_assets:
        raise_error("No SkeletalMesh assets found under /Game (excluding /Game/Weapons).")

    log("Listing all SkeletalMesh assets found (excluding /Game/Weapons):")
    for a in skeletal_assets:
        unreal.log(f"  {a.object_path}")

    keywords = ["mannequin", "character", "player", "man", "human", "said"]
    chosen = None
    for a in skeletal_assets:
        name_lower = a.asset_name.lower()
        if any(k in name_lower for k in keywords):
            chosen = a
            break
    if not chosen:
        chosen = skeletal_assets[0]  # fallback to first

    log(f"Selected skeletal mesh: {chosen.object_path}")
    skeletal_mesh = unreal.EditorAssetLibrary.load_asset(chosen.object_path)
    if not skeletal_mesh:
        raise_error(f"Failed to load selected skeletal mesh at {chosen.object_path}")
    return skeletal_mesh

# ---------- Step 3: Add Weapon Socket ----------
def add_weapon_socket(skeletal_mesh, static_mesh):
    # Get skeleton
    skeleton = skeletal_mesh.get_editor_property("skeleton")
    if not skeleton:
        raise_error("Selected skeletal mesh has no skeleton.")

    # List bone names
    bone_names = skeleton.get_reference_skeleton().get_bone_names()
    log("Bone names in skeleton:")
    for bn in bone_names:
        unreal.log(f"  {bn}")

    # Find right hand bone
    hand_keywords = ["hand_r", "righthand", "hand_r", "hand_r", "hand_r"]
    right_hand_bone = None
    for bn in bone_names:
        bn_str = bn.to_string().lower()
        if ("hand_r" in bn_str) or ("rhand" in bn_str) or ("righthand" in bn_str):
            right_hand_bone = bn
            break
    if not right_hand_bone:
        raise_error("Could not locate a right hand bone in the skeleton.")

    log(f"Using bone '{right_hand_bone}' for WeaponSocket.")

    # Create socket
    socket = unreal.SkeletalMeshSocket()
    socket.socket_name = "WeaponSocket"
    socket.bone_name = right_hand_bone
    # Small offset so the rifle sits nicely (adjust as needed)
    socket.relative_location = unreal.Vector(0.0, 0.0, 0.0)
    socket.relative_rotation = unreal.Rotator(0.0, 0.0, 0.0)
    socket.preview_mesh = static_mesh

    # Add socket to skeletal mesh
    skeletal_mesh.add_socket(socket)
    # Mark asset dirty and save
    unreal.EditorAssetLibrary.save_asset(skeletal_mesh.get_path_name())
    log("WeaponSocket added to skeletal mesh and preview asset set.")
    return socket

# ---------- Step 4: Add Weapon Component to Player Blueprint ----------
def add_weapon_component_to_blueprint(static_mesh):
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    blueprint_assets = [
        a for a in registry.get_assets_by_class("Blueprint")
        if a.object_path.startswith("/Game") and
           any(k in a.asset_name.lower() for k in ["character", "player"])
    ]

    if not blueprint_assets:
        log("No player character Blueprint found (searching for names containing 'character' or 'player'). Skipping step 4.")
        return

    for bp_asset in blueprint_assets:
        try:
            blueprint = unreal.EditorAssetLibrary.load_asset(bp_asset.object_path)
            if not blueprint:
                raise_error(f"Failed to load Blueprint at {bp_asset.object_path}")

            # Ensure we have a generated class
            if not blueprint.generated_class:
                raise_error(f"Blueprint {bp_asset.object_path} has no generated class.")

            # Add StaticMeshComponent
            component_name = "Weapon"
            component_class = unreal.StaticMeshComponent
            log(f"Adding StaticMeshComponent '{component_name}' to Blueprint {bp_asset.object_path}")
            new_comp = unreal.BlueprintEditorLibrary.add_component_to_blueprint(
                blueprint, component_class, component_name
            )
            if not new_comp:
                raise_error(f"Failed to create component '{component_name}' in Blueprint {bp_asset.object_path}")

            # Set mesh
            new_comp.set_editor_property("static_mesh", static_mesh)

            # Find parent SkeletalMeshComponent to attach to
            parent_comps = unreal.BlueprintEditorLibrary.get_all_components_of_class(
                blueprint, unreal.SkeletalMeshComponent
            )
            if not parent_comps:
                raise_error(f"No SkeletalMeshComponent found in Blueprint {bp_asset.object_path} to attach weapon to.")
            parent_comp = parent_comps[0]

            # Attach to socket
            new_comp.attach_to_component(parent_comp, "WeaponSocket", unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET, True)

            # Save Blueprint
            unreal.EditorAssetLibrary.save_asset(bp_asset.object_path)
            log(f"Weapon component added and attached to socket on Blueprint {bp_asset.object_path}")

        except Exception as e:
            unreal.log_warning(f"Failed to modify Blueprint {bp_asset.object_path}: {e}")
            continue  # continue with next blueprint if any

# ---------- Main Execution ----------
def main():
    try:
        # Step 1
        static_mesh = import_ak45()

        # Step 2
        skeletal_mesh = find_human_skeletal_mesh()

        # Step 3
        add_weapon_socket(skeletal_mesh, static_mesh)

        # Step 4 (optional)
        add_weapon_component_to_blueprint(static_mesh)

        # Step 5: Save everything
        log("Saving all dirty assets in /Game...")
        unreal.EditorAssetLibrary.save_directory("/Game", only_if_is_dirty=True)
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
        log("All assets saved successfully.")

    except Exception as err:
        unreal.log_error(f"Script failed: {err}")
        raise  # re‑raise to make failure visible

# Run the script
if __name__ == "__main__":
    main()