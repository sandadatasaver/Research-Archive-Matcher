#!/usr/bin/env python3
"""
PDF Page Extractor and Combiner
Reads a text file with PDF names and page numbers, extracts those pages,
and combines them into a single PDF in the specified order.

Text file format: filename.pdf p.X
Where p.X is the page number (1-indexed)
Example: A12.pdf p.3 means extract page 3 from A12.pdf
"""

import os
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter


def parse_instruction_file(instruction_file: str) -> list[tuple[str, int]]:
    """
    Parse the instruction file and return a list of (pdf_filename, page_number) tuples.
    
    Args:
        instruction_file: Path to the text file with instructions
        
    Returns:
        List of tuples: [(filename, page_number), ...]
    """
    instructions = []
    
    with open(instruction_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse the line
            parts = line.split()
            
            if len(parts) != 2:
                print(f"Warning: Line {line_num} has invalid format: '{line}'")
                print("Expected format: 'filename.pdf p.X'")
                continue
            
            pdf_filename = parts[0]
            page_spec = parts[1]
            
            # Validate PDF filename
            if not pdf_filename.lower().endswith('.pdf'):
                print(f"Warning: Line {line_num} - '{pdf_filename}' doesn't end with .pdf")
                continue
            
            # Parse page number
            if not page_spec.lower().startswith('p.'):
                print(f"Warning: Line {line_num} - '{page_spec}' doesn't start with 'p.'")
                continue
            
            try:
                page_num = int(page_spec[2:])  # Extract number after 'p.'
                
                if page_num < 1:
                    print(f"Warning: Line {line_num} - Page number must be >= 1: {page_num}")
                    continue
                
                instructions.append((pdf_filename, page_num))
                
            except ValueError:
                print(f"Warning: Line {line_num} - Invalid page number: '{page_spec}'")
                continue
    
    return instructions


def extract_and_combine_pdfs(
    instructions: list[tuple[str, int]],
    output_file: str,
    pdf_folder: str = '.'
) -> None:
    """
    Extract specified pages from PDFs and combine them into a single PDF.
    For each entry, always extracts page 1 (cover) first, then the specified page.
    
    Args:
        instructions: List of (pdf_filename, page_number) tuples
        output_file: Path for the output combined PDF
        pdf_folder: Folder containing the source PDFs (default: current directory)
    """
    writer = PdfWriter()
    pdf_cache = {}  # Cache opened PDFs to avoid reopening
    errors = []
    
    print(f"Processing {len(instructions)} page extractions...")
    print("Note: Each entry will extract page 1 (cover) first, then the specified page.\n")
    
    for i, (pdf_filename, page_num) in enumerate(instructions, 1):
        pdf_path = os.path.join(pdf_folder, pdf_filename)
        
        # Check if PDF file exists
        if not os.path.exists(pdf_path):
            errors.append(f"File not found: {pdf_filename}")
            print(f"[{i}/{len(instructions)}] ❌ File not found: {pdf_filename}")
            continue
        
        try:
            # Open PDF (use cache to avoid reopening same file multiple times)
            if pdf_filename not in pdf_cache:
                pdf_cache[pdf_filename] = PdfReader(pdf_path)
            
            reader = pdf_cache[pdf_filename]
            total_pages = len(reader.pages)
            
            # Check if page number is valid (convert to 0-indexed)
            page_index = page_num - 1
            
            if page_index >= total_pages:
                errors.append(f"{pdf_filename}: Page {page_num} doesn't exist (file has {total_pages} pages)")
                print(f"[{i}/{len(instructions)}] ⚠️  {pdf_filename} p.{page_num} - Page doesn't exist (has {total_pages} pages)")
                continue
            
            # Always extract page 1 (cover) first
            writer.add_page(reader.pages[0])  # Page 1 is index 0
            
            # Then extract the specified page (but not if it's also page 1)
            if page_index > 0:  # Only add if it's not page 1
                writer.add_page(reader.pages[page_index])
                print(f"[{i}/{len(instructions)}] ✅ {pdf_filename} → p.1 (cover) + p.{page_num}")
            else:
                print(f"[{i}/{len(instructions)}] ✅ {pdf_filename} → p.1 (cover only)")
            
        except Exception as e:
            errors.append(f"{pdf_filename}: Error processing - {str(e)}")
            print(f"[{i}/{len(instructions)}] ❌ Error processing {pdf_filename}: {e}")
            continue
    
    # Write the combined PDF
    if len(writer.pages) == 0:
        print("\n❌ No pages were successfully extracted. Output file not created.")
        return
    
    try:
        with open(output_file, 'wb') as output_pdf:
            writer.write(output_pdf)
        
        print(f"\n✅ Successfully created: {output_file}")
        print(f"   Total pages extracted: {len(writer.pages)}")
        print(f"   Note: Each entry extracted page 1 (cover) first, then the specified page.")
        
        if errors:
            print(f"\n⚠️  {len(errors)} error(s) occurred:")
            for error in errors:
                print(f"   - {error}")
    
    except Exception as e:
        print(f"\n❌ Error writing output file: {e}")


def main():
    """Main function to handle command-line arguments and run the script."""
    
    if len(sys.argv) < 3:
        print("PDF Page Extractor and Combiner")
        print("=" * 50)
        print("\nUsage:")
        print("  python pdf_extractor.py <instruction_file> <output_file> [pdf_folder]")
        print("\nArguments:")
        print("  instruction_file  - Text file with PDF names and page numbers")
        print("  output_file       - Output PDF filename")
        print("  pdf_folder        - Folder containing PDFs (optional, default: current folder)")
        print("\nInstruction file format:")
        print("  filename.pdf p.X  where X is the page number (1-indexed)")
        print("\nExample:")
        print("  python pdf_extractor.py instructions.txt combined.pdf ./pdfs")
        print("\nInstruction file example:")
        print("  A12.pdf p.3")
        print("  B05.pdf p.1")
        print("  C23.pdf p.7")
        print("  A12.pdf p.3")
        sys.exit(1)
    
    instruction_file = sys.argv[1]
    output_file = sys.argv[2]
    pdf_folder = sys.argv[3] if len(sys.argv) > 3 else '.'
    
    # Validate instruction file exists
    if not os.path.exists(instruction_file):
        print(f"❌ Instruction file not found: {instruction_file}")
        sys.exit(1)
    
    # Validate pdf folder exists
    if not os.path.isdir(pdf_folder):
        print(f"❌ PDF folder not found: {pdf_folder}")
        sys.exit(1)
    
    print("PDF Page Extractor and Combiner")
    print("=" * 50)
    print(f"Instruction file: {instruction_file}")
    print(f"Output file: {output_file}")
    print(f"PDF folder: {pdf_folder}")
    print()
    
    # Parse instructions
    instructions = parse_instruction_file(instruction_file)
    
    if not instructions:
        print("❌ No valid instructions found in the instruction file.")
        sys.exit(1)
    
    print(f"Found {len(instructions)} valid instruction(s).\n")
    
    # Extract and combine PDFs
    extract_and_combine_pdfs(instructions, output_file, pdf_folder)


if __name__ == '__main__':
    main()
