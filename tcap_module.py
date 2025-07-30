
import math
import numpy as np


bpy = None


# 斜切り円柱を1つだけ作成するためのプログラム
class Make_Cylinder:
    def __init__(self, num_vertices=128):
        # 円は正何角形で描画するかをここで指定
        # shade_auto_smoothを使用する場合は16程度でよい
        # shade_auto_smoothを使用しない場合は64以上は欲しい
        self.num_vertices = num_vertices
    
    # これを呼び出す
    def make_cylinder(self, mirror_height, cylinder_ends_angle, ior=1.52, isTruncatedCylinder=True):
        # 円柱（1つ）を作成
        lens, mirror, mask = self.make_cylinder_lens(mirror_height, cylinder_ends_angle, isTruncatedCylinder)
        # マテリアルを設定
        self.attachGlassMaterial(lens, mat_name = 'CylinderGlass', ior=ior)
        self.attachMirrorMaterial(mirror, mat_name = 'CylinderMirror')
        self.attachDarkMaterial(mask, mat_name = 'DarkCover')
        
        # 円柱を縮小して頂点の重なりを解消する
        lens.scale = (0.99, 0.99, 0.99)
        lens.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        lens.select_set(False)
        
        return [lens, mirror, mask]
    
    
    # 円柱（1つ）を作成
    def make_cylinder_lens(self, mirror_height, cylinder_ends_angle, isTruncatedCylinder=True):
        # 上面の頂点を作成
        num_vertices = self.num_vertices
        upper_vertices = []    # 上面の頂点
        lower_vertices = []    # 下面の頂点
        for i in range(num_vertices):
            angle = i * 2.0 * math.pi / num_vertices
            x = 0.5 * math.cos(angle)
            y = 0.5 * math.sin(angle)
            z = (mirror_height / 2.0) + (x + 0.5) * math.tan(cylinder_ends_angle)
            upper_vertices.append([x, y, z])
            lower_vertices.append([x, y, -z])
        vertices = upper_vertices + lower_vertices
        # 上面と下面の楕円面
        upper_faces = [[i for i in range(num_vertices)]]
        lower_faces = [[i for i in range(num_vertices * 2 - 1, num_vertices - 1, -1)]]
        faces = upper_faces + lower_faces
        # 側面
        for i in range(num_vertices):
            upper_num = [i for i in range(num_vertices)]
            lower_num = [i for i in range(num_vertices, num_vertices * 2)]
            face = [upper_num[i-1], lower_num[i-1], lower_num[i], upper_num[i]]
            faces.append(face)
            
        # 円柱メッシュを追加
        mesh = bpy.data.meshes.new('cylinder_lens_mesh')
        mesh.from_pydata(vertices, [], faces)
        # オブジェクトにアタッチ
        obj = bpy.data.objects.new('Cylinder_Lens', mesh)
        bpy.context.collection.objects.link(obj)
        obj.location = (0, 0, 0)
        
        # 鏡メッシュを追加
        mirror_mesh = bpy.data.meshes.new('cylinder_lens_mirror_mesh')
        if (isTruncatedCylinder):
            mirror_faces = faces[3+num_vertices//4 : 3+3*num_vertices//4]
            mirror_mesh.from_pydata(vertices, [], mirror_faces)
        else:
            mirror_mesh.from_pydata(vertices, [], faces[2:])
        # オブジェクトにアタッチ
        mirror_obj = bpy.data.objects.new('Cylinder_Lens_Mirror', mirror_mesh)
        bpy.context.collection.objects.link(mirror_obj)
        obj.location = (0, 0, 0)
        
        # 両端の切断面のマスク部分のメッシュを追加
        dark_mesh = bpy.data.meshes.new('cylinder_lens_cover')
        dark_faces = faces[0:2]
        dark_mesh.from_pydata(vertices, [], dark_faces)
        # オブジェクトにアタッチ
        dark_obj = bpy.data.objects.new('Cylinder_Lens_dark', dark_mesh)
        bpy.context.collection.objects.link(dark_obj)
        obj.location = (0, 0, 0)
        
        obj.rotation_euler = (0, 0, -math.pi / 2.0)
        mirror_obj.rotation_euler = (0, 0, -math.pi / 2.0)
        dark_obj.rotation_euler = (0, 0, -math.pi / 2.0)
        
        return [obj, mirror_obj, dark_obj]


    ##### MMAPs_Moduleから拝借 #####
    def attachMirrorMaterial(self, obj, mat_name):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            # Create materials
            mat = bpy.data.materials.new(name=mat_name)
        
        # Enable to use node
        mat.use_nodes = True
        # Clear nodes of material
        nodes = mat.node_tree.nodes
        nodes.clear()

        # Create princpled bsdf node
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Metallic'].default_value = 0.87
        bsdf.inputs['Roughness'].default_value = 0.01
        bsdf.location = 0,0

        # Create output node
        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        node_output.location = 400, 0

        # Link nodes
        links = mat.node_tree.links
        link = links.new(bsdf.outputs['BSDF'], node_output.inputs['Surface'])

        # Clear material of object
        obj.data.materials.clear()
        # Set material to object
        obj.data.materials.append(mat)


    def attachGlassMaterial(self, obj, mat_name, ior=1.52):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            # Create materials
            mat = bpy.data.materials.new(name=mat_name)
        
        # Enable to use node
        mat.use_nodes = True
        # Clear nodes of material
        nodes = mat.node_tree.nodes
        nodes.clear()

        # Create princpled bsdf node
        bsdf = nodes.new(type='ShaderNodeBsdfGlass')
        bsdf.inputs['Roughness'].default_value = 0.01
        bsdf.inputs['IOR'].default_value = ior
        bsdf.location = 0,0

        # Create output node
        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        node_output.location = 400, 0

        # Link nodes
        links = mat.node_tree.links
        link = links.new(bsdf.outputs['BSDF'], node_output.inputs['Surface'])

        # Clear material of object
        obj.data.materials.clear()
        # Set material to object
        obj.data.materials.append(mat)
    
    ##########
    def attachDarkMaterial(self, obj, mat_name):
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            # Create materials
            mat = bpy.data.materials.new(name=mat_name)
        
        # Enable to use node
        mat.use_nodes = True
        # Clear nodes of material
        nodes = mat.node_tree.nodes
        nodes.clear()

        # Create princpled bsdf node
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Metallic'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 1.0
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
        bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
        bsdf.location = 0,0

        # Create output node
        node_output = nodes.new(type='ShaderNodeOutputMaterial')
        node_output.location = 400, 0

        # Link nodes
        links = mat.node_tree.links
        link = links.new(bsdf.outputs['BSDF'], node_output.inputs['Surface'])

        # Clear material of object
        obj.data.materials.clear()
        # Set material to object
        obj.data.materials.append(mat)


# 与えられたオブジェクトを複製し二次元的に並べるプログラム
class Duplicate_Lens:
    
    # 格子状に配置する場合これを呼び出す
    def make_array_tetra(self, original_obj, numX, numY, interval=0):
        cylinder_line = self.line_up_cylinder(original_obj, original_obj.name + "_line", 1, 0, numX, interval)
        cylinder_ary = self.line_up_cylinder(cylinder_line, original_obj.name + "_array", 0, 1, numY, interval)
        bpy.data.objects.remove(cylinder_line)
        return cylinder_ary
    
    # MMAPのように斜めに配置された格子状に配置する場合はこれを呼び出す
    def make_array_tetra_diagonal(self, original_obj, numX, numY, interval=0):
        width_interval = (math.sqrt(2) * (1.0 + interval)) - 1.0
        numX = (int)(numX / math.sqrt(2))
        numY = (int)(numY / math.sqrt(2))
        cylinder_line = self.line_up_cylinder(original_obj, original_obj.name + "_line", 1, 0, numX, width_interval)
        cylinder_ary = self.line_up_cylinder(cylinder_line, original_obj.name + "_array", 0, 1, numY, width_interval)
        width_offset = (1.0 + interval) / math.sqrt(2)
        self.duplicate_move_and_rename(cylinder_ary, -width_offset, -width_offset, 0)
        bpy.data.objects.remove(cylinder_line)
        
        obj_list = []
        obj_list.append(bpy.context.selected_objects[0])
        obj_list.append(cylinder_ary)
        cylinder_ary = self.join_object(obj_list, cylinder_ary.name)
        return cylinder_ary
    
    # 六法細密構造のように密集して配置する場合
    def make_array_hex(self, original_obj, numX, numY, interval=0):
        numY = int(numY * 2.0 / math.sqrt(3))
        cylinder_line = self.line_up_cylinder(original_obj, original_obj.name + "_line", 1, 0, numX, interval)
        height_interval = (0.5 + (interval / 2.0)) * math.sqrt(3)
        cylinder_ary = self.line_up_cylinder(cylinder_line, original_obj.name + "_array", 0, 1, numY // 2, 2 * height_interval - 1.0)
        width_offset = 0.5 + (interval / 2.0)
        self.duplicate_move_and_rename(cylinder_ary, -width_offset, -height_interval, 0)
        bpy.data.objects.remove(cylinder_line)
        
        obj_list = []
        obj_list.append(bpy.context.selected_objects[0])
        obj_list.append(cylinder_ary)
        cylinder_ary = self.join_object(obj_list, cylinder_ary.name)
        return cylinder_ary


    def duplicate_move_and_rename(self, obj, x, y, z):
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        #print(original_obj)
        bpy.ops.object.duplicate_move(TRANSFORM_OT_translate={"value":(x,y,z)})


    # 指定したオブジェクトの子オブジェクトをすべて結合する
    def join_object(self, object_array, object_name):
        last_obj = None    # 最後のオブジェクトを記録するための変数
        # すべての子オブジェクトについて
        for children_obj in object_array:
            # 子オブジェクトを選択する
            children_obj.select_set(True)
        active_obj = object_array[0]
        # 最後のオブジェクトをアクティブオブジェクトにする
        bpy.context.view_layer.objects.active = active_obj
        # オブジェクトを結合
        bpy.ops.object.join()
        # Rename joined object
        active_obj.name = object_name
        # 結合したオブジェクトは選択解除
        active_obj.select_set(False)
        return active_obj


    # x, yずつずらしながら配置
    def line_up_cylinder(self, original_object, newName, x, y, count, interval=0):
        cylinder_ary = []
        for i in range(0, count, 1):
            self.duplicate_move_and_rename(original_object, x * i * (interval + 1), y * i * (interval + 1), 0)
            cylinder_ary.append(bpy.context.selected_objects[0])

        joined_obj = self.join_object(cylinder_ary, newName)
        original_object.hide_set(True)
        original_object.hide_render = True
        return joined_obj


class CylinderArrayModule:
    
    def __init__(self,
        mirror_height,          # 円柱の中央部分（切断しない部分）の長さ
        cylinder_ends_angle,    # 円柱両端の切断角度
        ior,                    # 屈折率
        diameter = 1,           # 円柱の直径
        width = 100,            # 円柱アレイの横幅
        height = 100,           # 円柱アレイの縦幅
        spacing = 0.0,          # 円柱同士の間隔（0で間隔なし、1で円柱1個分の間隔）
        mirror_ratio = 1,       # 鏡面部分の円柱高さに占める割合（斜切り円柱の時は1、通常の円柱の時は0.0から1.0未満）
        packing_mode = "tetra",    # 円柱充填方法（tetra, tetra_diagonal, hex）
        num_polygon_circle = 16,     # 円を何角形でモデリングするか
        shade_auto_smooth = True     # use shade auto smooth
    ):
        self.MakeCylinder = Make_Cylinder(num_polygon_circle)
        self.DuplicateLens = Duplicate_Lens()
        
        self.mirror_height = mirror_height
        self.cylinder_ends_angle = cylinder_ends_angle
        self.ior = ior
        self.diameter = diameter
        self.width = width
        self.height = height
        self.interval = spacing
        self.mirror_ratio = mirror_ratio
        self.packing_mode = packing_mode
        self.shade_auto_smooth = shade_auto_smooth
        
    
    # 円柱の直径は1であるとした場合の値を指定すること
    def make_cylinder_array(self, join=False):
        self.join = join
        
        lens = None
        mirror = None
        mask = None
        if (self.mirror_ratio == 1):    # 斜切り円柱の場合
            lens, mirror, mask = self.MakeCylinder.make_cylinder(self.mirror_height, self.cylinder_ends_angle, self.ior)
        else:    # 普通の円柱（先行特許）の場合
            lens, mirror, mask = self.MakeCylinder.make_cylinder(self.mirror_height, self.cylinder_ends_angle, self.ior, isTruncatedCylinder=False)
            mirror.scale = (1, 1, self.mirror_ratio)
            mirror.select_set(True)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            mirror.select_set(False)
            
        numX = int(self.width / (self.diameter + self.diameter * self.interval))
        numY = int(self.height / (self.diameter + self.diameter * self.interval))
        
        if (self.packing_mode == "tetra"):
            func_make_array = self.DuplicateLens.make_array_tetra
        elif (self.packing_mode == "tetra_diagonal"):
            func_make_array = self.DuplicateLens.make_array_tetra_diagonal
        elif (self.packing_mode == "hex"):
            func_make_array = self.DuplicateLens.make_array_hex
        
        # 軽量化のためここで結合
        lens_array = None
        if (join):
            lens.select_set(True)
            mirror.select_set(True)
            mask.select_set(True)
            bpy.context.view_layer.objects.active = lens
            bpy.ops.object.join()
            
            lens_array = func_make_array(lens, numX, numY, self.interval)
            
            # v0.2
            lens_array.location = (0.5, 0.5, 0.0)
            self.join_objects([lens_array], location=True)

            lens_array.scale = (self.diameter, self.diameter, self.diameter)
            self.delete_object(lens)
            
            lens_array.location = (-self.width / 2.0, -self.height / 2.0, 0)
            lens_array.name = 'TCA'
            lens_array.select_set(True)
            
            self.lens = lens_array

        else:
            lens_array = func_make_array(lens, numX, numY, self.interval)
            mirror_array = func_make_array(mirror, numX, numY, self.interval)
            mask_array = func_make_array(mask, numX, numY, self.interval)
            
            # v0.2
            lens_array.location = mirror_array.location = mask_array.location = (0.5, 0.5, 0.0)
            self.join_objects([lens_array, mirror_array, mask_array], location=True)
            
            lens_array.scale = (self.diameter, self.diameter, self.diameter)
            mirror_array.scale = (self.diameter, self.diameter, self.diameter)
            mask_array.scale = (self.diameter, self.diameter, self.diameter)
            
            self.delete_object(lens)
            self.delete_object(mirror)
            self.delete_object(mask)
            
            self.lens = lens_array
            self.mirror = mirror_array
            self.mask = mask_array
            
            # Move the optical elements center and apply transform
            lens_array.location = mirror_array.location = mask_array.location = (-self.width / 2.0, -self.height / 2.0, 0)
            lens_array.select_set(True)
            mirror_array.select_set(True)
            mask_array.select_set(True)
        
        bpy.context.view_layer.objects.active = lens_array
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        
        if (self.shade_auto_smooth):
            #bpy.ops.object.shade_smooth(use_auto_smooth=True)
            bpy.ops.object.shade_smooth()
            bpy.ops.object.use_auto_smooth = True
    
    
    def join_objects(self, object_list, location=False, rotation=False, scale=False):
        for obj in object_list:
            obj.select_set(True)
        bpy.ops.object.transform_apply(location=location, rotation=rotation, scale=scale)
        for obj in object_list:
            obj.select_set(False)
    
    
    def delete_object(self, object=None):
        if object is None:
            if (self.join):
                self.delete_object(self.lens)
            else:
                self.delete_object(self.lens)
                self.delete_object(self.mirror)
                self.delete_object(self.mask)
        else:
            bpy.context.collection.objects.unlink(object)
            bpy.data.objects.remove(object)


def make(bpy_, mirror_height, ends_angle, ior, diameter=0.5, width=50, height=50, space=0.0, packing_mode="tetra_diagonal", num_polygon_circle=256):

    global bpy
    bpy = bpy_
    
    cylinder_array_module = CylinderArrayModule(
        mirror_height = mirror_height,
        cylinder_ends_angle = ends_angle,
        ior = ior,
        diameter = diameter,
        width = width,
        height = height,
        spacing = space,
        packing_mode = packing_mode,
        num_polygon_circle = num_polygon_circle,
        shade_auto_smooth = False
    )
    cylinder_array_module.make_cylinder_array(join=True)
