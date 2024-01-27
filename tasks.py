from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive
from RPA.Assistant import Assistant

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    #open_the_intranet_website()
    user_input_task()
    download_csv()
    process_all_orders()
    archive_receipts()

def user_input_task():
    assistant = Assistant()
    assistant.add_heading("Input from user")
    assistant.add_text_input("text_input", placeholder="Please enter URL")
    assistant.add_submit_buttons("Submit", default="Submit")
    result = assistant.run_dialog()
    url = result.text_input
    # https://robotsparebinindustries.com/#/robot-order
    open_the_intranet_website(url)

def open_the_intranet_website(url):
    browser.goto(url)
    page = browser.page()
    page.set_viewport_size({"width": 1920, "height": 1080})

def close_annoying_modal():
    page = browser.page()
    page.click("button:text('OK')")

def download_csv():
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite=True)

def process_all_orders():
    orders = get_orders()
    for order in orders:
        close_annoying_modal()
        fill_the_form(order)
        submit_the_order(order)

def get_orders():
    library = Tables()
    orders = library.read_table_from_csv('orders.csv', columns=['Order number', 'Head', 'Body', 'Legs', 'Address'])
    return orders

def fill_the_form(order):
    page = browser.page()
    page.select_option('#head', order['Head'])
    selector = f"input[type='radio'][value='{order['Body']}']"
    page.click(selector)
    selector = f"input[class='form-control']"
    page.fill(selector, order['Legs'])
    page.fill('#address', order['Address'])
    page.click('#preview')

def submit_the_order(order):
    page = browser.page()
    page.click('#order')
    state = page.locator('div[class="alert alert-danger"]').is_visible()
    while state == True:
        print('alert')
        page.wait_for_timeout(500)
        page.click('#order')
        state = page.locator('div[class="alert alert-danger"]').is_visible()

    page.wait_for_timeout(500)
    page.wait_for_selector('#order-completion')
    save_screenshot()
    store_the_receipt_as_a_pdf_file()
    embed_the_robot_screenshot_to_the_receipt_PDF_file('output/receipt.pdf', 'output/robot_preview.png', order['Order number'])
    page.click('#order-another')

def save_screenshot():
    page = browser.page()
    buffer = page.locator('#robot-preview-image').screenshot()
    with open('output/robot_preview.png', "wb") as f:
        f.write(buffer)

def store_the_receipt_as_a_pdf_file():
    pdf = PDF()
    page = browser.page()
    receipt_html = page.inner_html('#receipt')
    #print(receipt_html)
    pdf.html_to_pdf(receipt_html, "output/receipt.pdf")

def embed_the_robot_screenshot_to_the_receipt_PDF_file(r, s, o):
    pdf = PDF()
    list_of_files = [
        r,
        s,
    ]
    pdf.add_files_to_pdf(files=list_of_files, target_document="output/final_receipt_{}.pdf".format(o))

def archive_receipts():
    lib = Archive()
    lib.archive_folder_with_zip('output', 'output/PDFs.zip', include='final_receipt_*')
