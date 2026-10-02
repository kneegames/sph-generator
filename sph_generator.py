#!/usr/bin/env python3
"""
SPH Generator - Simple web application for generating Surat Penawaran Harga
from Word template with PDF output.
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from docxtpl import DocxTemplate
import mammoth
from weasyprint import HTML
import tempfile
import uuid

app = Flask(__name__)
app.secret_key = 'sph_generator_secret_key_2026'

# Configuration
TEMPLATE_PATH = 'SPH/Draft SPH.docx'
OUTPUT_DIR = 'generated_sph'
ALLOWED_EXTENSIONS = {'docx'}

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_sph_filename(nama_pt, tanggal_surat):
    """Generate filename in format: SPH_PT_xxx_tanggal.pdf"""
    # Clean nama_pt for filename (remove special characters, spaces)
    clean_nama_pt = "".join(c for c in nama_pt if c.isalnum() or c in (' ', '-', '_')).rstrip()
    clean_nama_pt = clean_nama_pt.replace(' ', '_')
    
    # Format tanggal (assuming input is YYYY-MM-DD)
    try:
        tanggal_obj = datetime.strptime(tanggal_surat, '%Y-%m-%d')
        formatted_tanggal = tanggal_obj.strftime('%d%m%Y')
    except:
        formatted_tanggal = datetime.now().strftime('%d%m%Y')
    
    filename = f"SPH_PT_{clean_nama_pt}_{formatted_tanggal}.pdf"
    return filename

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_sph():
    try:
        # Get form data
        nama_pt = request.form.get('nama_pt', '').strip()
        lokasi = request.form.get('lokasi', '').strip()
        tanggal_surat = request.form.get('tanggal_surat', '').strip()
        jenis_sertifikasi = request.form.getlist('jenis_sertifikasi')
        biaya_ppiu = request.form.get('biaya_ppiu', '0').strip()
        biaya_pihk = request.form.get('biaya_pihk', '0').strip()
        keterangan = request.form.get('keterangan', '').strip()
        
        # Validation
        if not nama_pt:
            flash('Nama PT harus diisi', 'error')
            return redirect(url_for('index'))
        
        if not lokasi:
            flash('Lokasi harus diisi', 'error')
            return redirect(url_for('index'))
            
        if not tanggal_surat:
            flash('Tanggal surat harus diisi', 'error')
            return redirect(url_for('index'))
            
        if not jenis_sertifikasi:
            flash('Jenis sertifikasi harus dipilih', 'error')
            return redirect(url_for('index'))
        
        # Calculate totals
        biaya_ppiu_num = float(biaya_ppiu) if biaya_ppiu else 0
        biaya_pihk_num = float(biaya_pihk) if biaya_pihk else 0
        total_biaya = biaya_ppiu_num + biaya_pihk_num
        
        # Prepare context for template
        context = {
            'nama_pt': nama_pt,
            'lokasi': lokasi,
            'tanggal_surat': tanggal_surat,
            'jenis_sertifikasi': ', '.join(jenis_sertifikasi),
            'biaya_ppiu': f"{biaya_ppiu_num:,.0f}",
            'biaya_pihk': f"{biaya_pihk_num:,.0f}",
            'total_biaya': f"{total_biaya:,.0f}",
            'keterangan': keterangan
        }
        
        # Generate unique ID for this request
        request_id = str(uuid.uuid4())[:8]
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
            temp_docx_path = temp_docx.name
        
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
            temp_html_path = temp_html.name
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        try:
            # Load template and render
            doc = DocxTemplate(TEMPLATE_PATH)
            doc.render(context)
            doc.save(temp_docx_path)
            
            # Convert docx to HTML using mammoth
            with open(temp_docx_path, "rb") as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html = result.value  # The generated HTML
                # Optionally, you can log warnings: result.messages
            
            # Write HTML to temporary file
            with open(temp_html_path, "w", encoding="utf-8") as f:
                f.write(html)
            
            # Convert HTML to PDF using weasyprint
            HTML(string=html).write_pdf(temp_pdf_path)
            
            # Generate filename
            filename = generate_sph_filename(nama_pt, tanggal_surat)
            output_path = os.path.join(OUTPUT_DIR, filename)
            
            # Copy to output directory
            import shutil
            shutil.copy2(temp_pdf_path, output_path)
            
            # Send file for download
            return send_file(
                output_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_docx_path)
                os.unlink(temp_html_path)
                os.unlink(temp_pdf_path)
            except:
                pass
                
    except Exception as e:
        flash(f'Error generating SPH: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Check if template exists
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: Template file not found at {TEMPLATE_PATH}")
        print("Please ensure the SPH template is in the SPH/ folder")
        exit(1)
    
    print("SPH Generator starting...")
    print(f"Template loaded from: {TEMPLATE_PATH}")
    print("Access the application at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)