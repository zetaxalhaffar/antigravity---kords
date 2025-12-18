import os

def generate_landing_page(data):
    """
    Generates a single-page HTML landing page for the project.
    data: Dictionary containing project details from the scraper.
    """
    project_name = data.get("Project Name", "Real Estate Project")
    description = data.get("Description", "")
    description_lines = description.split('\n') if description else []
    
    # Format description (take first 2 paragraphs as lead, rest as details)
    desc_html = ""
    for line in description_lines[:20]: # Limit for main view
        if line.strip():
            desc_html += f"<p>{line}</p>"

    master_plan_path = data.get("Master Plan Path")
    gallery_paths = data.get("Gallery Paths", [])
    output_dir = data.get("Output Dir")
    
    # Relative paths for HTML
    mp_rel = os.path.basename(master_plan_path) if master_plan_path else ""
    gallery_rel = [os.path.basename(p) for p in gallery_paths]

    # Hero Image (use first gallery image or generic)
    hero_bg = gallery_rel[0] if gallery_rel else ""

    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #1a1a1a;
            --accent: #c6a466; /* Gold/Bronze accent */
            --light: #f5f5f5;
            --text: #333;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Cairo', sans-serif;
            color: var(--text);
            background-color: #fff;
            line-height: 1.6;
        }}

        h1, h2, h3 {{ font-weight: 700; color: var(--primary); }}

        /* Hero Section */
        .hero {{
            height: 100vh;
            background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url('{hero_bg}') no-repeat center center/cover;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: white;
            position: relative;
        }}

        .hero h1 {{
            font-size: 3.5rem;
            margin-bottom: 1rem;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }}

        .hero-scroll {{
            position: absolute;
            bottom: 30px;
            animation: bounce 2s infinite;
        }}
        
        @keyframes bounce {{
            0%, 20%, 50%, 80%, 100% {{transform: translateY(0);}}
            40% {{transform: translateY(-10px);}}
            60% {{transform: translateY(-5px);}}
        }}

        /* Container */
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        /* About Section */
        .section-title {{
            font-size: 2.5rem;
            margin-bottom: 2rem;
            text-align: center;
            position: relative;
            padding-bottom: 15px;
        }}
        
        .section-title::after {{
            content: '';
            display: block;
            width: 60px;
            height: 3px;
            background: var(--accent);
            margin: 10px auto 0;
        }}

        .about-content {{
            display: flex;
            gap: 40px;
            align-items: start;
        }}

        .about-text {{ flex: 1; font-size: 1.1rem; text-align: justify; }}
        .about-text p {{ margin-bottom: 15px; }}
        
        .about-image {{
            flex: 1;
            box-shadow: 20px 20px 0 var(--accent);
        }}
        
        .about-image img {{
            width: 100%;
            display: block;
            border-radius: 4px;
        }}

        /* Master Plan */
        .master-plan {{
            background: var(--light);
            padding: 80px 0;
        }}
        
        .mp-container {{ text-align: center; }}
        .mp-container img {{
            max-width: 100%;
            border: 5px solid white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            cursor: zoom-in;
            transition: transform 0.3s;
        }}
        
        .mp-container img:hover {{ transform: scale(1.02); }}

        /* Gallery */
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }}
        
        .gallery-item {{
            height: 250px;
            overflow: hidden;
            border-radius: 4px;
        }}
        
        .gallery-item img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.5s;
        }}
        
        .gallery-item:hover img {{ transform: scale(1.1); }}

        /* Footer */
        footer {{
            background: var(--primary);
            color: white;
            text-align: center;
            padding: 30px;
            margin-top: 50px;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .hero h1 {{ font-size: 2.5rem; }}
            .about-content {{ flex-direction: column; }}
            .about-image {{ box-shadow: 10px 10px 0 var(--accent); }}
        }}
    </style>
</head>
<body>

    <!-- Hero -->
    <header class="hero">
        <div>
            <h1>{project_name}</h1>
            <p style="font-size: 1.2rem;">اكتشف الفخامة في قلب الطبيعة</p>
        </div>
        <div class="hero-scroll">⬇</div>
    </header>

    <!-- About -->
    <section class="container">
        <h2 class="section-title">عن المشروع</h2>
        <div class="about-content">
            <div class="about-text">
                {desc_html}
            </div>
            <div class="about-image">
                <img src="{gallery_rel[1] if len(gallery_rel) > 1 else hero_bg}" alt="Project View">
            </div>
        </div>
    </section>

    <!-- Master Plan -->
    {f'''
    <section class="master-plan">
        <div class="container mp-container">
            <h2 class="section-title">المخطط العام (Master Plan)</h2>
            <img src="{mp_rel}" alt="Master Plan">
        </div>
    </section>
    ''' if mp_rel else ''}

    <!-- Gallery -->
    <section class="container">
        <h2 class="section-title">معرض الصور</h2>
        <div class="gallery-grid">
            {''.join([f'<div class="gallery-item"><img src="{img}" loading="lazy"></div>' for img in gallery_rel])}
        </div>
    </section>

    <footer>
        <p>&copy; 2024 {project_name}. All rights reserved.</p>
    </footer>

</body>
</html>
"""
    
    # Write to index.html in output directory
    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"Landing page generated: {output_path}")
    return output_path
