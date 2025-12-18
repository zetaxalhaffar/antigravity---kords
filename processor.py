import pandas as pd
import os

def process_excel_file(input_path, output_dir_or_path):
    """
    Reads an Excel file, splits by Project, filters columns, renames them, and saves.
    
    Returns:
        (bool, list_of_paths): Success status and list of generated files.
    """
    try:
        print(f"Processing file: {input_path}")
        df = pd.read_excel(input_path)
        
        # 1. Column Mapping Logic
        mapping_rules = {
            'code': ['Unit Id', 'Unit ID', 'unit id'],
            'sale_type': ['Sale Type', 'Sale', 'sale type', 'sale'],
            'size': ['BU area', 'BU Area', 'bu area'],
            'beds_no': ['Beds', 'beds'],
            'baths_no': ['Baths', 'baths'],
            'Floor Number': ['Floor Number', 'floor', 'Floor'],
            'badget': ['Price 1', 'price 1', 'Price1']
        }
        
        # Project Column Candidates
        project_col_candidates = ['Project', 'Project Name', 'project', 'project name', 'Project name']
        
        def find_col(candidates, dataframe):
            for cand in candidates:
                if cand in dataframe.columns:
                    return cand
            return None

        # Build rename dict
        rename_dict = {}
        for target_name, candidates in mapping_rules.items():
            found = find_col(candidates, df)
            if found:
                rename_dict[found] = target_name

        # 2. Identify Projects
        found_project_col = find_col(project_col_candidates, df)
        
        # If output directed to a file path (not dir), we might be in single file mode, 
        # but the requirement is to split. We will assume output_dir_or_path is a directory 
        # or we treat the parent dir as the target.
        
        if os.path.isfile(output_dir_or_path) or output_dir_or_path.endswith('.xlsx'):
             output_dir = os.path.dirname(output_dir_or_path)
        else:
             output_dir = output_dir_or_path
             
        generated_files = []

        # Helper to process a dataframe chunk
        def save_chunk(sub_df, p_name):
             # Filter cols
             cols_to_keep = list(rename_dict.keys())
             chunk_filtered = sub_df[cols_to_keep].copy()
             chunk_filtered.rename(columns=rename_dict, inplace=True)
             
             # Sanitize name
             safe_name = "".join([c for c in str(p_name) if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
             if not safe_name: safe_name = "Untitled"
             
             filename = f"{safe_name}.xlsx"
             full_path = os.path.join(output_dir, filename)
             
             chunk_filtered.to_excel(full_path, index=False)
             print(f"Saved: {full_path}")
             return full_path

        if found_project_col:
            # Check for Size column as well (mapped to 'size')
            # We need to know which column in the original DF maps to 'size'
            found_size_col = None
            size_candidates = mapping_rules['size']
            found_size_col = find_col(size_candidates, df)

            if found_size_col:
                # Group by Project AND Size
                groups = df.groupby([found_project_col, found_size_col])
                print(f"Splitting by Project and Size. Found {len(groups)} groups.")
                
                for (proj, size_val), sub_df in groups:
                    # Construct composite name
                    safe_proj = "".join([c for c in str(proj) if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
                    safe_size = "".join([c for c in str(size_val) if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
                    
                    if not safe_proj: safe_proj = "Untitled"
                    if not safe_size: safe_size = "UnknownSize"
                    
                    composite_name = f"{safe_proj} - {safe_size}"
                    path = save_chunk(sub_df, composite_name)
                    generated_files.append(path)
            else:
                # Fallback to Project only if size not found
                unique_projects = df[found_project_col].dropna().unique()
                print(f"Found projects (no size col): {unique_projects}")
                
                for proj in unique_projects:
                    sub_df = df[df[found_project_col] == proj]
                    path = save_chunk(sub_df, proj)
                    generated_files.append(path)
        else:
            # No project column, save as one file
            # Use original filename or default
            base_name = os.path.basename(input_path)
            name_no_ext = os.path.splitext(base_name)[0]
            # remove 'temp_' prefix if present for cleaner name
            if name_no_ext.startswith('temp_'):
                name_no_ext = name_no_ext[5:]
                
            path = save_chunk(df, name_no_ext)
            generated_files.append(path)

        return True, generated_files

    except Exception as e:
        print(f"Error processing file {input_path}: {e}")
        return False, []

# For testing independently
if __name__ == "__main__":
    # Create a dummy file for testing
    dummy_data = {
        'Unit Id': [101, 102, 103],
        'Sale Type': ['Sell', 'Rent', 'Sell'],
        'BU area': [120, 150, 100],
        'Beds': [2, 3, 1],
        'Baths': [2, 2, 1],
        'floor': [1, 2, 3],
        'Price 1': [100000, 200000, 300000],
        'Project': ['Skyline Tower', 'Ocean View', 'Skyline Tower']
    }
    df = pd.DataFrame(dummy_data)
    df.to_excel("test_input_split.xlsx", index=False)
    
    # Test passing directory
    os.makedirs("output_files", exist_ok=True)
    success, paths = process_excel_file("test_input_split.xlsx", "output_files")
    print(f"Result paths: {paths}")
