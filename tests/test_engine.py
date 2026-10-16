from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from engine import classify_file,unique_path,SUPPORTED_OUTPUTS,convert_file
from PIL import Image
import fitz

def test_classification():
    assert classify_file('teste.DOCX')=='office'
    assert classify_file('teste.PDF')=='pdf'
    assert classify_file('teste.mp4')=='video'
    assert classify_file('teste.unknown') is None

def test_unique(tmp_path):
    p=tmp_path/'teste.txt';p.write_text('1')
    assert unique_path(p).name=='teste (2).txt'

def test_image_to_pdf_and_jpg(tmp_path):
    image=tmp_path/'entrada.png';Image.new('RGBA',(80,40),(0,180,50,140)).save(image)
    folder=tmp_path/'saida'
    jpg=convert_file(image,'JPG',folder)[0]
    pdf=convert_file(image,'PDF',folder)[0]
    assert jpg.exists() and pdf.exists()
    with fitz.open(pdf) as d:assert len(d)==1
    files=convert_file(pdf,'PNG',folder)
    assert len(files)==1 and files[0].exists()

def test_pdf_to_text(tmp_path):
    doc=fitz.open();p=doc.new_page();p.insert_text((80,80),'Teste de exportacao')
    path=tmp_path/'origem.pdf';doc.save(path);doc.close()
    result=convert_file(path,'TXT',tmp_path/'saida')[0]
    assert 'Teste de exportacao' in result.read_text(encoding='utf-8')
