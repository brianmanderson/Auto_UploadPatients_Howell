__author__ = 'Brian M Anderson'
# Created on 5/15/2020

"""
First, we identify the plans and corresponding images
"""

run_local = False
if run_local:
    from Run_Locally import Split_Plan_RT
    data_path = r'L:\Research\Howell'  # some path to plan folders
    out_path = r'Y:\Exports'  # Some path to where we can locally write them and upload to RS
    split = Split_Plan_RT(out_path=out_path)
    split.down_folder(data_path)
    for path in split.dicom_folders:
        split.identify_MRNs(path)
    for MRN in split.patient_folders.keys():
        print('Coping over {}'.format(MRN))
        split.combine_plan_RTs(MRN)

"""
Next, Raystation will query PACS for the corresponding images and import them, along with the plans
Run_On_Raystation.py
"""