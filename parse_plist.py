#!/usr/bin/python
#-*-coding:utf8-*-

import os
import sys  
from xml.etree import ElementTree  
from PIL import Image  
import fnmatch
import Tkinter
import tkFileDialog
import tkMessageBox
import sitecustomize


def tree_to_dict(tree):  
    
    d = {}  
    for index, item in enumerate(tree):  
        if item.tag == 'key':  
            if tree[index+1].tag == 'string':  
                d[item.text] = tree[index + 1].text  
            elif tree[index+1].tag == 'integer':  
                d[item.text] = int(tree[index + 1].text)  
            elif tree[index + 1].tag == 'true':  
                d[item.text] = True  
            elif tree[index + 1].tag == 'false':  
                d[item.text] = False  
            elif tree[index+1].tag == 'dict':  
                d[item.text] = tree_to_dict(tree[index+1])  
                
    return d  


def gen_png_from_plist(plist_filename, png_filename, save_path):

    # 解析plist为字典
    file_path = plist_filename.replace('.plist', '')
    root = ElementTree.fromstring(open(plist_filename, 'r').read())
    big_image = Image.open(png_filename)      
    plist_dict = tree_to_dict(root[0])
    to_list = lambda x: x.replace('{','').replace('}','').split(',')
    
    format_version = int(plist_dict["metadata"]["format"])
    
    # 判断plist类型 有的plist的用 frame 有的用 aliases 关键有的frame还不一样  这里我先做我面对的几种不一样的情况
    for k, v in plist_dict['frames'].items():
        
        if format_version == 3:
            # pack后剩下的有效区域
            texture_rect = [ int(x) for x in to_list(v["textureRect"]) ]
            # 是否旋转
            isRotate = v["textureRotated"]      
            # 获得长宽
            width = int( texture_rect[3] if isRotate else texture_rect[2] )  
            height = int( texture_rect[2] if isRotate else texture_rect[3] ) 
            
            # 小图在大图上的位置
            offset = [ int(x) for x in to_list( v["spriteOffset"]) ]        
            source_size = [ int(x) for x in to_list(v["spriteSourceSize"]) ]        
            
            # 图像大小
            rect_box = ( texture_rect[0], texture_rect[1], texture_rect[0] + width, texture_rect[1] + height )
            if isRotate:
                result_box=(  
                    ( source_size[0] - height)/2 + offset[0],  
                    ( source_size[1] - width)/2 - offset[1],  
                    ( source_size[0] + height)/2 + offset[0],  
                    ( source_size[1] + width)/2 - offset[1]   
                    )  
            else:
                result_box=(  
                    ( source_size[0] - width)/2 + offset[0],  
                    ( source_size[1] - height)/2 - offset[1],  
                    ( source_size[0] + width)/2 + offset[0],  
                    ( source_size[1] + height)/2 - offset[1] 
                    )              
        else:        
            # pack后剩下的有效区域
            texture_rect = [ int(x) for x in to_list(v["frame"]) ]
            # 是否旋转
            isRotate = v["rotated"]   
            # 获得长宽
            width = int( texture_rect[3] if isRotate else texture_rect[2] )  
            height = int( texture_rect[2] if isRotate else texture_rect[3] )  
           
            # 小图在大图上的位置
            source_size = [ int(x) for x in to_list(v['sourceSize'])]  
    
            # 图像大小
            rect_box = (int(texture_rect[0]),  int(texture_rect[1]),  int(texture_rect[0]) + width,  int(texture_rect[1]) + height)  
            if isRotate:  
                result_box=(  
                    ( source_size[0] - height ) / 2,  
                    ( source_size[1] - width ) / 2,  
                    ( source_size[0] + height ) / 2,  
                    ( source_size[1] + width ) / 2  
                )  
            else:  
                result_box=(  
                    ( source_size[0] - width ) / 2,  
                    ( source_size[1] - height ) / 2,  
                    ( source_size[0] + width ) / 2,  
                    ( source_size[1] + height ) / 2  
                )  
        
        new_rect_image = big_image.crop(rect_box)  
        if isRotate: new_rect_image = new_rect_image.rotate(90, expand=1)       
        
        result_image = Image.new('RGBA', source_size, (0,0,0,0)) 
        result_image.paste(new_rect_image, result_box)  

        if save_path != None and len(save_path) > 0:
            if os.path.basename(k) == k:
                outfile = os.path.join(save_path, os.path.basename(file_path), k)
            else:
                outfile = os.path.join(save_path, k) 
        else:
            outfile = os.path.join(file_path, k)

        ##因为原本的plist 的图片目录并不一定只有1级，所以需要多次创建目录  
        newpath = os.path.dirname(outfile)  
        if not os.path.isdir(newpath):  
            os.makedirs(newpath)  

        print outfile, "generated file"  
        result_image.save(outfile)  


def batch_parse(src_path, dest_path, filterext = "*.plist"):
    
    parse_count = 0
    
    for dirpath, dirnames, filenames in os.walk(src_path): 
 
        dest_dir = '.' + dirpath[len(src_path):]
        new_dest_path = os.path.join(dest_path, dest_dir)
        
        for filename in filenames:
            
            if fnmatch.fnmatch(filename, filterext):  
  
                plist_file_path = os.path.join(dirpath, filename)
                png_file_path = os.path.join(dirpath, os.path.splitext(filename)[0] + ".png")
                
                if os.path.exists(plist_file_path) and os.path.exists(png_file_path):

                    try:
                        print plist_file_path
                        print png_file_path   
                        gen_png_from_plist(plist_file_path, png_file_path, dest_path)  
                        parse_count += 1
                    except:
                        print "parse error!!!"

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