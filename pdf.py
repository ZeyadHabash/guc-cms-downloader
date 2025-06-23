import fitz  # PyMuPDF
import os
import argparse

def extract_pdf_images(pdf_path, output_dir):
    """
    Extracts all unique images from a PDF and saves them to a specified output directory.

    Args:
        pdf_path (str): The full path to the PDF file.
        output_dir (str): The directory where the extracted images will be saved.
    """
    try:
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        extracted_xrefs = set()  # Track unique image XREFs
        image_counter = 1  # Global image counter for unique images

        # Iterate through each page of the PDF
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)

            # Get the list of images on the page
            image_list = page.get_images(full=True)

            # If no images are found on the page, skip to the next
            if not image_list:
                continue

            print(f"Found {len(image_list)} images on page {page_number + 1} of {os.path.basename(pdf_path)}")

            # Iterate through the images on the page
            for image_index, img in enumerate(image_list, start=1):
                # Get the XREF of the image
                xref = img[0]

                # Only extract if this XREF hasn't been extracted before
                if xref in extracted_xrefs:
                    continue
                extracted_xrefs.add(xref)

                # Extract the image bytes
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Define the image filename (global unique index)
                image_filename = f"image_{image_counter}.{image_ext}"
                image_filepath = os.path.join(output_dir, image_filename)

                # Save the image
                with open(image_filepath, "wb") as image_file:
                    image_file.write(image_bytes)
                    print(f"  - Saved: {image_filename}")
                image_counter += 1

    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
    finally:
        if 'pdf_document' in locals() and pdf_document:
            pdf_document.close()

def main():
    """
    Main function to parse arguments and process PDF files in a directory.
    """
    parser = argparse.ArgumentParser(description="Extract images from all PDFs in a directory.")
    parser.add_argument("input_dir", help="The directory containing PDF files.")
    args = parser.parse_args()

    input_directory = args.input_dir

    if not os.path.isdir(input_directory):
        print(f"Error: Input directory '{input_directory}' not found.")
        return

    # Iterate through all files in the input directory
    for filename in os.listdir(input_directory):
        if filename.lower().endswith(".pdf"):
            pdf_filepath = os.path.join(input_directory, filename)
            # Create a folder name based on the PDF file name (without extension)
            output_folder_name = os.path.splitext(filename)[0]
            output_folder_path = os.path.join(input_directory, output_folder_name)

            print(f"\nProcessing: {filename}")
            extract_pdf_images(pdf_filepath, output_folder_path)

    print("\nImage extraction complete.")

if __name__ == "__main__":
    main()