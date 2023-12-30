#!/usr/bin/python3
#-*-coding:utf8-*-

import os
import sys  
from xml.etree import ElementTree  
from PIL import Image  
import fnmatch
if sys.version[0] == '2':
    import Tkinter
    import tkFileDialog
    import tkMessageBox
    import sitecustomize
else:
    import tkinter as Tkinter
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox  


class PlistUnpacker:

    def Tree2Dict(self, tree):  
        
        data = {}  
        for index, item in enumerate(tree):  
            if item.tag == 'key':  
                if tree[index + 1].tag == 'string':  
                    data[item.text] = tree[index + 1].text  
                elif tree[index + 1].tag == 'integer':  
                    data[item.text] = int(tree[index + 1].text)
                elif tree[index + 1].tag == 'real':  
                    data[item.text] = float(tree[index + 1].text)                     
                elif tree[index + 1].tag == 'true':  
                    data[item.text] = True  
                elif tree[index + 1].tag == 'false':  
                    data[item.text] = False  
                elif tree[index + 1].tag == 'dict':  
                    data[item.text] = self.Tree2Dict(tree[index + 1])  
                    
        return data  


    def GenImagesFromPlist(self, plist_filename, save_path):
    
        # 解析plist为字典
        print("parse plist file:", plist_filename)
        root = {}
        with open(plist_filename, 'r') as fd:
            root = ElementTree.fromstring(fd.read())
            
        plist_dict = self.Tree2Dict(root[0])
        format_version = None
        real_texture_filename = ""
        texture_filename = ""
        if "metadata" in plist_dict:
            if "format" in plist_dict["metadata"]:
                format_version = int(plist_dict["metadata"]["format"])
            
            if "realTextureFileName" in plist_dict["metadata"]:
                real_texture_filename = plist_dict["metadata"]["realTextureFileName"]
                
            if "textureFileName" in plist_dict["metadata"]:
                texture_filename = plist_dict["metadata"]["textureFileName"]
            
            if len(real_texture_filename) == 0 and len(texture_filename) > 0:
                real_texture_filename = texture_filename
                
        else:
            error_msg = "plist file format error, filename: " + plist_filename
            print(error_msg)
            raise error_msg            
        
        plist_dir = os.path.dirname(plist_filename)
        image_filepath = os.path.join(plist_dir, real_texture_filename)
        print("plist texture image file:", image_filepath)  
        if not os.path.exists(image_filepath):
            error_msg = "plist texture image file not exist, filename: " + image_filepath
            print(error_msg)
            raise error_msg
        
        plist_image = Image.open(image_filepath)
        
        # 判断plist类型 有的plist的用 frame 有的用 aliases 关键有的frame还不一样  这里我先做我面对的几种不一样的情况
        to_list = lambda text: text.replace('{','').replace('}','').split(',')
        for result_image_filename, dict_data in plist_dict['frames'].items():
            if format_version == 3:
                # 小图在大图上的位置
                texture_rect = [int(x) for x in to_list(dict_data["textureRect"])]
                # 是否旋转
                is_rotate = dict_data["textureRotated"]      
                # 获得宽高
                width = int(texture_rect[3] if is_rotate else texture_rect[2])  
                height = int(texture_rect[2] if is_rotate else texture_rect[3]) 
                
                # 原图信息
                offset = [int(x) for x in to_list( dict_data["spriteOffset"])]
                source_color_rect = [int(x) for x in to_list(dict_data["spriteColorRect"])] 
                source_size = [int(x) for x in to_list(dict_data["spriteSourceSize"])]
                
            elif format_version == 2 or format_version == 1:        
                # 小图在大图上的位置
                texture_rect = [int(x) for x in to_list(dict_data["frame"])]
                # 是否旋转
                is_rotate = dict_data["rotated"]   
                # 获得宽高
                width = int(texture_rect[3] if is_rotate else texture_rect[2])  
                height = int(texture_rect[2] if is_rotate else texture_rect[3])  
               
                # 原图信息
                offset = [int(x) for x in to_list(dict_data["offset"])]
                source_color_rect = [int(x) for x in to_list(dict_data["sourceColorRect"])] 
                source_size = [int(x) for x in to_list(dict_data["sourceSize"])]  
    
            elif format_version == 0:
                # 小图在大图上的位置
                texture_rect = [int(dict_data['x']), int(dict_data['y']), int(dict_data['width']), int(dict_data['height'])]
                # 是否旋转
                is_rotate = False   
                # 获得宽高
                width = int(texture_rect[3] if is_rotate else texture_rect[2])  
                height = int(texture_rect[2] if is_rotate else texture_rect[3])  
               
                # 原图信息
                offset = [int(dict_data["offsetX"]), int(dict_data["offsetY"])]
                source_color_rect = [int(dict_data["offsetX"]), int(dict_data["offsetY"]), int(dict_data['width']), int(dict_data['height'])] 
                source_size = [int(dict_data["originalWidth"]), int(dict_data["originalHeight"])]
                
            else:
                error_msg = "this is plist format version:" + str(format_version) + ", not support!"
                print(error_msg)
                raise error_msg
        
            # 图像大小
            image_rect = (texture_rect[0],  texture_rect[1], texture_rect[0] + width, texture_rect[1] + height)
            image_color_rect = (source_color_rect[0], source_color_rect[1], source_color_rect[0] + source_color_rect[2], source_color_rect[1] + source_color_rect[3])
            if is_rotate:  
                image_color_rect = (  
                    int((source_size[0] - height) / 2 + offset[0]),  
                    int((source_size[1] - width) / 2 - offset[1]),  
                    int((source_size[0] + height) / 2 + offset[0]),  
                    int((source_size[1] + width) / 2 - offset[1])  
                )  
            else:  
                image_color_rect = (  
                    int((source_size[0] - width) / 2 + offset[0]),  
                    int((source_size[1] - height) / 2 - offset[1]),  
                    int((source_size[0] + width) / 2 + offset[0]),  
                    int((source_size[1] + height) / 2 - offset[1])  
                )
            
            new_image = plist_image.crop(image_rect)  
            if is_rotate: new_image = new_image.rotate(90, expand = 1)       
            
            result_image = Image.new('RGBA', source_size, (0,0,0,0)) 
            result_image.paste(new_image, image_color_rect)  
    
            save_image_dir = os.path.splitext(plist_filename)[0]
            result_image_filepath = ""
            if save_path != None and len(save_path) > 0:
                # 只有图像文件名称，则添加plist名称作为目录
                if os.path.basename(result_image_filename) == result_image_filename:
                    result_image_filepath = os.path.join(save_path, os.path.basename(save_image_dir), result_image_filename)
                else:
                    result_image_filepath = os.path.join(save_path, result_image_filename) 
            else:
                result_image_filepath = os.path.join(save_image_dir, result_image_filename)
    
            ##因为原本的plist 的图片目录并不一定只有1级，所以需要多次创建目录  
            result_image_dir = os.path.dirname(result_image_filepath)  
            if not os.path.isdir(result_image_dir):  
                os.makedirs(result_image_dir)  
     
            print("generated image file:", result_image_filepath)  
            result_image.save(result_image_filepath)  



def batch_parse(src_path, dest_path, filterext = "*.plist"):
    
    parse_count = 0
    for dirpath, dirnames, filenames in os.walk(src_path):
        
        for filename in filenames:
            
            if fnmatch.fnmatch(filename, filterext):  
                plist_filepath = os.path.join(dirpath, filename)
                
                if os.path.exists(plist_filepath):
                    try:
                        unpacker = PlistUnpacker()
                        unpacker.GenImagesFromPlist(plist_filepath, dest_path)  
                        parse_count += 1
                    except:
                        print("parse error!!!")

    return parse_count



class ParsePlistDlg(object):
    
    def __init__(self):
        
        self.dlg = Tkinter.Tk()
        self.dlg.title(u"解析Plist文件")
        self.dlg.geometry("580x120")
        self.dlg.resizable(width=False, height=False) 
        
        self.paned1 = Tkinter.PanedWindow(self.dlg, orient=Tkinter.HORIZONTAL)  
        self.paned1.pack(pady=10)        
        
        label = Tkinter.Label(self.paned1, text=u"解析目录：")   
        self.enter_source_path = Tkinter.Entry(self.paned1, width=50)
        self.btn_source_path = Tkinter.Button(self.paned1, text=u"浏览", command=self.OnBtnSourcePath)
        self.paned1.add(label)
        self.paned1.add(self.enter_source_path)
        self.paned1.add(self.btn_source_path)
    
        self.paned2 = Tkinter.PanedWindow(self.dlg, orient=Tkinter.HORIZONTAL)  
        self.paned2.pack()
    
        label = Tkinter.Label(self.paned2, text=u"保存目录：")    
        self.enter_target_path = Tkinter.Entry(self.paned2, width=50)   
        self.btn_target_path = Tkinter.Button(self.paned2, text=u"浏览", command=self.OnBtnTargetPath)
        self.paned2.add(label)
        self.paned2.add(self.enter_target_path)
        self.paned2.add(self.btn_target_path)
        
        self.btn_execute = Tkinter.Button(self.dlg, text=u"执行", command=self.OnBtnExecute)
        self.btn_execute.pack()
        
        
    def run(self):
        
        self.dlg.mainloop()
        
        
    def OnBtnSourcePath(self):
        
        select_dir = tkFileDialog.askdirectory()
        self.enter_source_path["state"] = "normal"
        self.enter_source_path.delete(0, Tkinter.END)
        self.enter_source_path.insert(0, select_dir) 
        self.enter_source_path["state"] = "readonly"
    
    def OnBtnTargetPath(self):
        
        select_dir = tkFileDialog.askdirectory()
        self.enter_target_path["state"] = "normal"
        self.enter_target_path.delete(0, Tkinter.END)
        self.enter_target_path.insert(0, select_dir)   
        self.enter_target_path["state"] = "readonly"  
        
    def OnBtnExecute(self):
        
        src_path = self.enter_source_path.get()
        dest_path = self.enter_target_path.get()
        
        if len(src_path) == 0 and not os.path.exists(src_path):
            tkMessageBox.showinfo(u"提示", u"解析目录为空或者不存在, 请重新选择目录！")
            return
        
        if len(dest_path) == 0 and not os.path.exists(dest_path):
            tkMessageBox.showinfo(u"提示", u"保存目录为空或者不存在, 请重新选择目录！")
            return
        
        self.btn_execute["state"] = Tkinter.DISABLED
        parse_count = batch_parse(src_path, dest_path)
        self.btn_execute["state"] = Tkinter.NORMAL
        
        if parse_count > 0:
            tkMessageBox.showinfo(u"提示", u"解析完成！")
        else:
            tkMessageBox.showinfo(u"提示", u"没有找到要解析的Plist文件！")


def main():
    
    """software start runing """
    
    app = ParsePlistDlg()
    app.run()


if __name__ == '__main__':  
    
    main()