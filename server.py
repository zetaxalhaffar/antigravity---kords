from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
import os
import zipfile
from processor import process_excel_file
from pydantic import BaseModel
import realty_scraper
import page_generator

app = FastAPI()

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse("static/index.html")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Ensure output directory exists
    output_dir = os.path.join(os.getcwd(), "output_files")
    os.makedirs(output_dir, exist_ok=True)

    temp_input = f"temp_{file.filename}"
    # Use a timestamp to avoid collisions
    output_filename = f"processed_{file.filename}"
    output_full_path = os.path.join(output_dir, output_filename)
    
    try:
        # Save uploaded file
        with open(temp_input, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Process it and save to the FINAL destination folder
        # We pass the directory, and the processor decides the filename based on Project Name
        # Note: we ignore output_full_path calculation from above as processor handles it now
        success, generated_files = process_excel_file(temp_input, output_dir)
        
        if success and generated_files:
            if len(generated_files) == 1:
                # Single file
                final_path = generated_files[0]
                filename = os.path.basename(final_path)
                return FileResponse(
                    path=final_path, 
                    filename=filename,
                    media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            else:
                # Multiple files -> Zip them
                zip_filename = f"processed_projects_{file.filename}.zip"
                zip_path = os.path.join(output_dir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file_path in generated_files:
                        zipf.write(file_path, arcname=os.path.basename(file_path))
                
                return FileResponse(
                    path=zip_path,
                    filename=zip_filename,
                    media_type='application/zip'
                )

        else:
            raise HTTPException(status_code=500, detail="Failed to process file")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup input file
        if os.path.exists(temp_input):
            os.remove(temp_input)
        # Note: We DO NOT delete the output file, as the user requested to save it there.

# Background cleanup could be added, but for simplicity in local use, we leave temp files 
# or clean them on startup.

from starlette.concurrency import run_in_threadpool

class ProjectURL(BaseModel):
    url: str

@app.post("/download-project")
async def download_project(project: ProjectURL):
    try:
        print(f"Received request to download: {project.url}")
        
        # 1. Scrape Data (Run Sync Playwright in ThreadPool)
        data_list = await run_in_threadpool(realty_scraper.run, project.url)
        
        if not data_list:
            raise HTTPException(status_code=400, detail="Failed to scrape data from URL. Check if URL is valid.")
            
        project_data = data_list[0]
        
        # 2. Skip Landing Page Generation (User Request)
        # page_path = page_generator.generate_landing_page(project_data)
        
        # 3. Zip the project directory
        output_dir = project_data.get("Output Dir")
        if not output_dir or not os.path.exists(output_dir):
             raise HTTPException(status_code=500, detail="Output directory not found after scraping")
             
        project_name = os.path.basename(output_dir)
        zip_filename = f"{project_name}.zip"
        zip_path = os.path.join(os.path.dirname(output_dir), zip_filename)
        
        # Create Zip
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', output_dir)
        
        # Return Zip
        return FileResponse(
            path=zip_path,
            filename=zip_filename,
            media_type='application/zip'
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing project: {e}")
        raise HTTPException(status_code=500, detail=str(e))
