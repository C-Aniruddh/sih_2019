# Autonomous Invoice Processing

Developed Smart India Hackathon 2019 - Problem statment code RV1, Orgranization : KG INFOSYSTEM PVT. LTD.
The tool uses Google Cloud Vision for OCR (which adds support for over 130 languages to this platform)

Demo Video : 

[![Demo Video](http://img.youtube.com/vi/uq4nnyigLMQ/0.jpg)](https://www.youtube.com/watch?v=uq4nnyigLMQ "Demo Video")

The flow is as follows : 

  - If the input is a PDF, we convert it into a JPEG, and perform text detection
  - Once we have a bounding box for each text, we look for key and value pairs within them
  - Then, the pdf is preprocessed, and tables are extracted for the same
  - There is support to view the extracted invoice information in the visualization section.

