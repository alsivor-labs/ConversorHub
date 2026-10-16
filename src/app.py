"""ConversorHub: Windows desktop front end for local file conversions."""
from __future__ import annotations
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from engine import (SUPPORTED_OUTPUTS, classify_file, convert_file, download_media,
                    check_dependencies, Cancelled, ConversionError)

ctk.set_appearance_mode('light')
ctk.set_default_color_theme('blue')
COLORS = {'bg':'#F5F7FB','card':'#FFFFFF','ink':'#182437','muted':'#65748B','line':'#E6EBF2','blue':'#276EF1','light':'#EAF2FF'}
APPDATA = Path(os.getenv('LOCALAPPDATA') or Path.home() / '.local' / 'share') / 'ConversorHub'
CONFIG = APPDATA / 'preferences.json'


def load_config():
    try: return json.loads(CONFIG.read_text(encoding='utf-8'))
    except Exception: return {}


def open_folder(path):
    folder = Path(path)
    if folder.is_file(): folder = folder.parent
    if sys.platform == 'win32': os.startfile(str(folder))
    elif sys.platform == 'darwin': subprocess.Popen(['open',str(folder)])
    else: subprocess.Popen(['xdg-open',str(folder)])


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('ConversorHub — conversões no seu computador')
        self.geometry('1210x800')
        self.minsize(970,650)
        self.configure(fg_color=COLORS['bg'])
        self.cfg=load_config()
        self.output_dir=ctk.StringVar(value=self.cfg.get('output_dir') or str(Path.home()/'Videos'/'ConversorHub'))
        self.url=ctk.StringVar()
        self.download_type=ctk.StringVar(value='Vídeo MP4')
        self.quality=ctk.StringVar(value='Melhor disponível')
        self.target_format=ctk.StringVar(value='PDF')
        self.queue=queue.Queue()
        self.pending=[]
        self.cancel=threading.Event()
        self.running=False
        self.files=[]
        self.history=list(self.cfg.get('history',[]))[:60]
        self.build_layout()
        self.show('Início')
        self.after(100,self.poll)
        self.protocol('WM_DELETE_WINDOW',self.close)

    def save(self):
        APPDATA.mkdir(parents=True,exist_ok=True)
        CONFIG.write_text(json.dumps({'output_dir':self.output_dir.get(),'history':self.history[:60]},ensure_ascii=False,indent=2),encoding='utf-8')

    def text(self,parent,value,size=13,bold=False,color=None,**kwargs):
        return ctk.CTkLabel(parent,text=value,text_color=color or COLORS['ink'],font=ctk.CTkFont(size=size,weight='bold' if bold else 'normal'),**kwargs)

    def build_layout(self):
        self.grid_columnconfigure(1,weight=1)
        self.grid_rowconfigure(0,weight=1)
        self.sidebar=ctk.CTkFrame(self,fg_color='#FFFFFF',corner_radius=0,width=211)
        self.sidebar.grid(row=0,column=0,sticky='nsew')
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar,text='◉  ConversorHub',text_color='#14243C',font=ctk.CTkFont(size=23,weight='bold')).pack(anchor='w',padx=21,pady=(31,8))
        self.text(self.sidebar,'ARQUIVOS • ÁUDIO • VÍDEO',10,color=COLORS['muted']).pack(anchor='w',padx=23,pady=(0,32))
        self.nav={}
        for label,icon in [('Início','⌂'),('Baixar mídia','↓'),('Converter arquivos','⇄'),('Histórico','◷'),('Configurações','⚙')]:
            btn=ctk.CTkButton(self.sidebar,text=f'  {icon}    {label}',anchor='w',height=45,corner_radius=10,
                fg_color='transparent',hover_color=COLORS['light'],text_color=COLORS['ink'],
                font=ctk.CTkFont(size=14),command=lambda s=label:self.show(s))
            btn.pack(fill='x',padx=14,pady=3)
            self.nav[label]=btn
        ctk.CTkLabel(self.sidebar,text='GRATUITO • PROCESSAMENTO LOCAL',font=ctk.CTkFont(size=10),text_color='#8896A9').pack(side='bottom',padx=12,pady=25)
        self.main=ctk.CTkScrollableFrame(self,fg_color='transparent',corner_radius=0)
        self.main.grid(row=0,column=1,sticky='nsew',padx=23,pady=15)
        self.main.grid_columnconfigure(0,weight=1)

    def clear(self):
        for widget in self.main.winfo_children():widget.destroy()

    def headline(self,title,desc):
        self.text(self.main,title,27,True).pack(anchor='w',pady=(15,5))
        self.text(self.main,desc,13,color=COLORS['muted']).pack(anchor='w',pady=(0,22))

    def card(self,parent=None):
        panel=ctk.CTkFrame(parent or self.main,fg_color='white',border_color=COLORS['line'],border_width=1,corner_radius=14)
        panel.pack(fill='x',pady=(0,17))
        return panel

    def show(self,screen):
        self.screen=screen
        self.clear()
        for n,b in self.nav.items():
            active=n==screen
            b.configure(fg_color=COLORS['light'] if active else 'transparent',text_color=COLORS['blue'] if active else COLORS['ink'])
        {'Início':self.home,'Baixar mídia':self.download_screen,'Converter arquivos':self.convert_screen,
         'Histórico':self.history_screen,'Configurações':self.settings_screen}[screen]()

    def home(self):
        self.headline('Tudo o que você precisa, em um só lugar','Baixe, converta e transforme arquivos no seu PC. Sem conta ou servidor.')
        grid=ctk.CTkFrame(self.main,fg_color='transparent');grid.pack(fill='x',pady=4)
        for i,(title,desc,where) in enumerate([
          ('↓  Baixar vídeo','Links compatíveis, MP4 e áudio','Baixar mídia'),
          ('▤  Documentos','Word, PowerPoint e Excel → PDF','Converter arquivos'),
          ('♫  Áudio e vídeo','MP3, WAV, MP4, GIF e mais','Converter arquivos'),
          ('▧  Imagens','JPG, PNG, WEBP e PDF','Converter arquivos')]):
            grid.grid_columnconfigure(i,weight=1)
            p=ctk.CTkFrame(grid,fg_color='white',border_width=1,border_color=COLORS['line'],corner_radius=12)
            p.grid(row=0,column=i,sticky='nsew',padx=5)
            self.text(p,title,15,True).pack(anchor='w',padx=16,pady=(22,6))
            self.text(p,desc,11,color=COLORS['muted'],wraplength=150,justify='left').pack(anchor='w',padx=16)
            ctk.CTkButton(p,text='Abrir →',command=lambda s=where:self.show(s),height=32).pack(anchor='w',padx=15,pady=17)
        self.text(self.main,'Como funciona',19,True).pack(anchor='w',pady=(27,12))
        box=self.card()
        self.text(box,'1. Escolha uma ferramenta      2. Adicione o arquivo ou link      3. Escolha a pasta      4. Inicie',13).pack(anchor='w',padx=20,pady=20)
        self.progress_panel()

    def directory_row(self,parent):
        self.text(parent,'Pasta de destino',13,True).pack(anchor='w',padx=20,pady=(19,5))
        row=ctk.CTkFrame(parent,fg_color='transparent');row.pack(fill='x',padx=20,pady=(0,17))
        ctk.CTkEntry(row,textvariable=self.output_dir,height=40,corner_radius=8).pack(side='left',fill='x',expand=True,padx=(0,9))
        ctk.CTkButton(row,text='Escolher pasta',width=125,height=40,command=self.choose_folder).pack(side='right')

    def choose_folder(self):
        val=filedialog.askdirectory(initialdir=self.output_dir.get() if Path(self.output_dir.get()).exists() else str(Path.home()),title='Escolha onde salvar')
        if val:self.output_dir.set(val);self.save()

    def download_screen(self):
        self.headline('Baixar vídeo ou áudio','Cole um link de conteúdo que você pode baixar. Um vídeo por vez, sem playlists.')
        panel=self.card()
        self.text(panel,'Endereço do conteúdo',13,True).pack(anchor='w',padx=20,pady=(20,8))
        ctk.CTkEntry(panel,textvariable=self.url,placeholder_text='https://...',height=45).pack(fill='x',padx=20)
        row=ctk.CTkFrame(panel,fg_color='transparent');row.pack(fill='x',padx=20,pady=(20,5))
        self.text(row,'Formato',12,True).pack(side='left',padx=(0,12))
        ctk.CTkOptionMenu(row,variable=self.download_type,values=['Vídeo MP4','Áudio MP3','Áudio M4A','Vídeo original'],width=177,height=39).pack(side='left')
        self.text(row,'Qualidade',12,True).pack(side='left',padx=(25,12))
        ctk.CTkOptionMenu(row,variable=self.quality,values=['Melhor disponível','1080p','720p','480p'],width=155,height=39).pack(side='left')
        self.directory_row(panel)
        ctk.CTkButton(panel,text='↓  Baixar',height=43,font=ctk.CTkFont(size=14,weight='bold'),command=self.start_download).pack(anchor='e',padx=20,pady=(0,20))
        self.progress_panel()
        self.text(self.main,'Use somente conteúdo próprio ou autorizado. A disponibilidade depende da plataforma.',11,color=COLORS['muted'],wraplength=760).pack(anchor='w',pady=(4,12))

    def convert_screen(self):
        self.headline('Converter arquivos','Documentos, imagens, áudio e vídeo — conversão no seu computador.')
        panel=self.card()
        self.text(panel,'Arquivos selecionados',13,True).pack(anchor='w',padx=20,pady=(19,5))
        self.selected_label=self.text(panel,'Nenhum arquivo adicionado',12,color=COLORS['muted'],anchor='w',justify='left',wraplength=730)
        self.selected_label.pack(fill='x',padx=20,pady=(0,9))
        row=ctk.CTkFrame(panel,fg_color='transparent');row.pack(fill='x',padx=20)
        ctk.CTkButton(row,text='+  Escolher arquivos',command=self.choose_files,height=38).pack(side='left')
        ctk.CTkButton(row,text='Limpar',command=self.clear_files,fg_color='#EDF1F7',text_color=COLORS['ink'],height=38,width=77).pack(side='left',padx=10)
        self.text(panel,'Converter para',13,True).pack(anchor='w',padx=20,pady=(21,5))
        self.format_menu=ctk.CTkOptionMenu(panel,variable=self.target_format,values=['PDF'],height=40,width=170)
        self.format_menu.pack(anchor='w',padx=20)
        self.directory_row(panel)
        ctk.CTkButton(panel,text='⇄  Converter arquivos',height=43,font=ctk.CTkFont(size=14,weight='bold'),command=self.start_convert).pack(anchor='e',padx=20,pady=(0,20))
        self.progress_panel()
        self.text(self.main,'Observação: PDF → Word pode precisar de revisão do layout. Documentos Office requerem LibreOffice.',11,color=COLORS['muted']).pack(anchor='w')

    def choose_files(self):
        files=filedialog.askopenfilenames(title='Arquivos para converter')
        if files:
            self.files=list(files)
            self.refresh_files()

    def clear_files(self):
        self.files=[]
        self.refresh_files()

    def refresh_files(self):
        if not self.files:
            self.selected_label.configure(text='Nenhum arquivo adicionado')
            self.format_menu.configure(values=['PDF']);self.target_format.set('PDF');return
        types={classify_file(p) for p in self.files}
        if None in types or len(types)!=1:
            self.selected_label.configure(text=f'{len(self.files)} arquivos selecionados. Selecione apenas arquivos da mesma categoria.')
            self.format_menu.configure(values=['PDF']);self.target_format.set('PDF');return
        opts=SUPPORTED_OUTPUTS[types.pop()]
        self.format_menu.configure(values=opts)
        self.target_format.set(opts[0])
        names=', '.join(Path(p).name for p in self.files[:3]);more=f' e mais {len(self.files)-3}' if len(self.files)>3 else ''
        self.selected_label.configure(text=names+more)

    def progress_panel(self):
        card=self.card()
        self.text(card,'Atividade',16,True).pack(anchor='w',padx=20,pady=(15,4))
        self.status=self.text(card,'Aguardando uma tarefa.',12,color=COLORS['muted'],anchor='w',wraplength=750,justify='left')
        self.status.pack(fill='x',padx=20,pady=(0,9))
        bar=ctk.CTkProgressBar(card,progress_color=COLORS['blue'],height=9)
        bar.pack(fill='x',padx=20)
        bar.set(0)
        self.bar=bar
        row=ctk.CTkFrame(card,fg_color='transparent');row.pack(anchor='e',padx=20,pady=(14,16))
        self.cancel_btn=ctk.CTkButton(row,text='Cancelar',fg_color='#EDF1F7',text_color=COLORS['ink'],width=90,height=34,state='disabled',command=self.cancel_task)
        self.cancel_btn.pack(side='left',padx=5)
        ctk.CTkButton(row,text='Abrir pasta',width=105,height=34,command=lambda:open_folder(self.output_dir.get())).pack(side='left')

    def begin(self,fn,label):
        if self.running:
            messagebox.showinfo('Tarefa em andamento','Aguarde ou cancele a tarefa atual.')
            return
        try: Path(self.output_dir.get()).expanduser().mkdir(parents=True,exist_ok=True)
        except Exception as e: messagebox.showerror('Pasta inválida',str(e));return
        self.save()
        self.running=True;self.cancel.clear()
        self.status.configure(text=f'Iniciando: {label}')
        self.bar.configure(mode='indeterminate');self.bar.start()
        self.cancel_btn.configure(state='normal')
        def work():
            try:
                outputs=fn()
                self.queue.put(('done', label, [str(p) for p in outputs]))
            except Cancelled as e:self.queue.put(('cancel',str(e)))
            except Exception as e:self.queue.put(('error',str(e)))
        threading.Thread(target=work,daemon=True).start()

    def start_download(self):
        url=self.url.get().strip()
        if not url:messagebox.showwarning('Link ausente','Cole o link de um vídeo.');return
        fmt=self.download_type.get()
        opts={'Vídeo MP4':'VIDEO MP4','Áudio MP3':'ÁUDIO MP3','Áudio M4A':'ÁUDIO M4A','Vídeo original':'VÍDEO ORIGINAL'}
        self.begin(lambda:download_media(url,self.output_dir.get(),opts[fmt],self.quality.get(),self.cancel,
                                            lambda msg:self.queue.put(('progress',msg))),f'Download: {fmt}')

    def start_convert(self):
        if not self.files:messagebox.showwarning('Arquivos ausentes','Escolha ao menos um arquivo.');return
        types={classify_file(p) for p in self.files}
        if len(types)!=1 or None in types:messagebox.showwarning('Arquivos incompatíveis','Selecione arquivos da mesma categoria.');return
        files=list(self.files);fmt=self.target_format.get();dest=self.output_dir.get()
        def do_work():
            all_results=[]
            for i,p in enumerate(files,1):
                if self.cancel.is_set():raise Cancelled('Tarefa cancelada.')
                self.queue.put(('progress',f'Convertendo {i}/{len(files)}: {Path(p).name}'))
                all_results.extend(convert_file(p,fmt,dest,self.cancel,lambda x:self.queue.put(('progress',x))))
            return all_results
        self.begin(do_work,f'{len(files)} arquivo(s) → {fmt}')

    def cancel_task(self):
        if self.running:
            self.cancel.set();self.status.configure(text='Cancelamento solicitado…')

    def poll(self):
        try:
            while True:
                item=self.queue.get_nowait();event=item[0]
                if event=='progress':
                    if self.winfo_exists() and hasattr(self,'status'):
                        self.status.configure(text=item[1][:240])
                elif event in ('done','error','cancel'):
                    self.running=False
                    if hasattr(self,'bar'):self.bar.stop();self.bar.configure(mode='determinate');self.bar.set(1 if event=='done' else 0)
                    if hasattr(self,'cancel_btn'):self.cancel_btn.configure(state='disabled')
                    if event=='done':
                        label,paths=item[1],item[2]
                        self.history.insert(0,{'date':datetime.now().strftime('%d/%m/%Y %H:%M'),'label':label,'paths':paths})
                        self.history=self.history[:60];self.save()
                        if hasattr(self,'status'):self.status.configure(text=f'Concluído. {len(paths)} arquivo(s) pronto(s).')
                    elif event=='error':
                        if hasattr(self,'status'):self.status.configure(text='Falha na tarefa.')
                        messagebox.showerror('Não foi possível concluir',item[1][-1600:])
                    else:
                        if hasattr(self,'status'):self.status.configure(text='Tarefa cancelada.')
        except queue.Empty:pass
        try:self.after(120,self.poll)
        except tk.TclError:pass

    def history_screen(self):
        self.headline('Histórico','Veja os arquivos processados neste computador.')
        if not self.history:self.text(self.main,'Nenhum arquivo processado ainda.',14,color=COLORS['muted']).pack(anchor='w');return
        for item in self.history:
            p=self.card()
            row=ctk.CTkFrame(p,fg_color='transparent');row.pack(fill='x',padx=18,pady=12)
            self.text(row,item.get('label','Conversão'),14,True).pack(anchor='w')
            self.text(row,item.get('date',''),11,color=COLORS['muted']).pack(anchor='w',pady=3)
            paths=item.get('paths',[])
            if paths:
                self.text(row,Path(paths[0]).name,12,color=COLORS['muted']).pack(anchor='w')
                ctk.CTkButton(row,text='Mostrar na pasta',width=130,command=lambda s=paths[0]:open_folder(s)).pack(anchor='e')

    def settings_screen(self):
        self.headline('Configurações','Tudo é processado localmente, sem criar conta.')
        panel=self.card()
        self.directory_row(panel)
        self.text(self.main,'Ferramentas detectadas',17,True).pack(anchor='w',pady=(4,11))
        data=check_dependencies()
        for name,present in data.items():
            row=self.card()
            self.text(row,('●   ' if present else '○   ')+name,14,True,color='#198754' if present else '#B55D1B').pack(anchor='w',padx=18,pady=12)
        self.text(self.main,'LibreOffice é necessário para DOCX/PPTX/XLSX → PDF; FFmpeg para conversões de áudio/vídeo. PDF para DOCX é uma conversão aproximada.',12,color=COLORS['muted'],wraplength=720,justify='left').pack(anchor='w')

    def close(self):
        if self.running and not messagebox.askyesno('Tarefa em andamento','Sair pode interromper a conversão. Deseja fechar?'):return
        self.cancel.set();self.save();self.destroy()


if __name__=='__main__': App().mainloop()
