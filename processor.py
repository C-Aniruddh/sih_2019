from pyimagesearch.transform import four_point_transform
from pyimagesearch import imutils
from skimage.filters import threshold_adaptive
import numpy as np
import cv2
import os
import camelot

import math
import subprocess

class Processor:

    def scan_form(self, form_name, form_image_path):

        # load the image and compute the ratio of the old height
        # to the new height, clone it, and resize it
        image = cv2.imread(form_image_path)
        ratio = image.shape[0] / 500.0
        orig = image.copy()
        image = imutils.resize(image, height=500)
        # convert the image to grayscale, blur it, and find edges
        # in the image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(gray, 75, 200)

        # show the original image and the edge detected image
        print("STEP 1: Edge Detection")
        # cv2.imshow("Image", image)
        # cv2.imshow("Edged", edged)

        # find the contours in the edged image, keeping only the
        # largest ones, and initialize the screen contour
        _, cnts, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        print("Found contours")

        # loop over the contours
        for c in cnts:
            # approximate the contour
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            # if our approximated contour has four points, then we
            # can assume that we have found our screen
            if len(approx) == 4:
                screenCnt = approx
                break
        # show the contour (outline) of the piece of paper
        print("STEP 2: Find contours of paper")
        cv2.drawContours(image, [screenCnt], -1, (0, 255, 0), 2)
        # cv2.imshow("Outline", image)

        # apply the four point transform to obtain a top-down
        # view of the original image
        warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

        # convert the warped image to grayscale, then threshold it
        # to give it that 'black and white' paper effect
        # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        # warped = threshold_adaptive(warped, 251, offset = 10)
        # warped = warped.astype("uint8") * 255

        # show the original and scanned images
        print("STEP 3: Apply perspective transform")
        # cv2.imshow("Original", orig)
        # cv2.imshow("Scanned", warped)


        print("SAVE")
        # cv2.imwrite("scanned.jpg", imutils.resize(warped, height = 450))
        # cv2.imwrite("scanned.jpg", warped)
        print("CROP")

        img = warped
        height, width, channels = img.shape
        end_h = int(height - 10)
        end_w = int(width - 10)

        crop_img = img[10:end_h, 10:end_w]

        print("SAVE CROP")

        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
        filename = '%s_scanned.jpg' % form_name
        final_filename = '%s/%s_scanned.jpg' % (UPLOAD_FOLDER, form_name)
        cv2.imwrite(final_filename, crop_img)

        print("Done")

        w = crop_img.shape[0]
        h = crop_img.shape[1]

        return w, h, filename, final_filename


    def get_form_details(self, form_name, image_path):
        image = cv2.imread(image_path)
        w = image.shape[0]
        h = image.shape[1]
        filename = '%s_scanned.jpg' % form_name
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
        final_filename = '%s/%s_scanned.jpg' % (UPLOAD_FOLDER, form_name)
        cv2.imwrite(final_filename, image)
        return w, h, filename, final_filename


    def process_pdf(self, form_name, invoice_file):
        invoice_filename = invoice_file.split('/')[-1]
        print(invoice_filename)
        print("In here")
        flag_invoice_file = '-%s' % (invoice_filename)
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/uploads')
        final_filename = '%s/%s_scanned.png' % (UPLOAD_FOLDER, form_name)
        args = ['convert', '-verbose', '-density 150', '-trim', flag_invoice_file, '-quality 100', '-flatten', '-sharpen 0x1.0', final_filename]
        convert_to_image = subprocess.call(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3600)
        print("Converting")
        print(convert_to_image)
        image = cv2.imread(final_filename)
        w = image.shape[0]
        h = image.shape[1]
        filename = '%s_scanned.jpg' % (form_name)
        return w, h, filename, final_filename


    def pdf2img(self, form_name, invoice_file):
        flag_invoice_file = '-%s' % (invoice_file)
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        UPLOAD_FOLDER = os.path.join(APP_ROOT, 'static/imgs')
        final_filename = '%s/%s_scanned.png' % (UPLOAD_FOLDER, form_name)
        command = 'magick convert -verbose -trim %s -quality 100 -flatten -sharpen 0x1.0 %s' %(invoice_file, final_filename)
        # args = ['magick', 'convert', '-verbose', '-trim', invoice_file, '-quality 100', '-flatten', '-sharpen 0x1.0', final_filename]
        # convert_to_image = subprocess.check_output(args)
        os.system(command)
        print("Converting")
        filename = '%s_scanned.jpg' % (form_name)
        return filename, final_filename


    def preprocess(self, image_file, form_code):
        img = cv2.imread(image_file)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        lsd = cv2.createLineSegmentDetector(0)
        dlines = lsd.detect(gray)

        for dline in dlines[0]:
            x0 = int(round(dline[0][0]))
            y0 = int(round(dline[0][1]))
            x1 = int(round(dline[0][2]))
            y1 = int(round(dline[0][3]))
            cv2.line(img, (x0, y0), (x1, y1), 255, 1, cv2.LINE_AA)

            # print line segment length
            a = (x0 - x1) * (x0 - x1)
            b = (y0 - y1) * (y0 - y1)
            c = a + b
            print(math.sqrt(c))



        APP_ROOT = os.path.dirname(os.path.abspath(__file__))

        TEXT_PDF = os.path.join(APP_ROOT, 'static/preprocessed')
        final_filename = '%s/%s_scanned.jpg' % (TEXT_PDF, form_code)
        cv2.imwrite(final_filename, img)

        return final_filename


    def convert_to_pdf(self, form_name, invoice_file):
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        TEXT_PDF = os.path.join(APP_ROOT, 'static/text_pdf')
        final_filename = '%s/%s_scanned.pdf' % (TEXT_PDF, form_name)

        TEMP_PDF = os.path.join(APP_ROOT, 'static/tmp_pdf')
        tmp_filename = '%s/%s_scanned.pdf' % (TEMP_PDF, form_name)

        # processed_file = self.preprocess(invoice_file, form_name)

        # comm1 = 'convert %s -quality 100 %s' % (processed_file, tmp_filename)
        # os.system(comm1)
        command = 'ocrmypdf --jobs 4 -l eng --deskew --oversample 300 --image-dpi 72 %s %s' %(invoice_file, final_filename)
        # subprocess.Popen(command)
        os.system(command)
        #args = ['ocrmypdf', '--jobs 4', '--deskew', '--image-dpi 72' , inv_file, out_file]
        #print(args)
        #convert_to_pdf = subprocess.check_output(args)
        # print(convert_to_pdf)
        print("Converted to pdf")
        filename = "%s_scanned.pdf" % (form_name)
        return filename, final_filename

    def get_table_details(self, form_name, invoice_file, sub_id):
        tables = camelot.read_pdf(invoice_file)
        # tables.export('auto.csv', f='csv', compress=True) # json, excel, html
        print(tables[0].parsing_report)
        tables[0].df
        APP_ROOT = os.path.dirname(os.path.abspath(__file__))
        TEXT_CSV = os.path.join(APP_ROOT, 'static/csv')
        fname = '%s_%s' % (form_name, sub_id)
        out_csv = "%s/%s.csv" % (TEXT_CSV, fname)
        tables[0].to_csv(out_csv)
        return tables, out_csv
   