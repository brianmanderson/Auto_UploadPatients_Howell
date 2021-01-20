__author__ = 'Brian M Anderson'
# Created on 5/15/2020

import pydicom
import os
import SimpleITK as sitk
import shutil
import difflib


class Split_Plan_RT(object):
    def __init__(self, out_path):
        self.dicom_folders = []
        self.patient_folders = {}
        self.out_path = out_path

    def down_folder(self, path):
        files = []
        dirs = []
        for root, dirs, files in os.walk(path):
            break
        files = [i for i in files if i.endswith('.dcm')]
        if files:
            print('Adding {}'.format(path))
            self.dicom_folders.append(path)
        for dir_val in dirs:
            self.down_folder(os.path.join(path,dir_val))
        return None

    def identify_MRNs(self, patient_path):
        files = [i for i in os.listdir(patient_path) if i.endswith('.dcm') and i.startswith('RTPLAN')]
        plan_keys = []
        for file in files:
            ds = pydicom.read_file(os.path.join(patient_path, file))
            MRN = ds.PatientID
            if MRN not in self.patient_folders:
                self.patient_folders[MRN] = {}
            plan_key = file.split(' - ')[1].split('.dcm')[0]
            plan_keys.append(plan_key)
            if plan_key not in self.patient_folders[MRN]:
                self.patient_folders[MRN][plan_key] = []
            self.patient_folders[MRN][plan_key].append(os.path.join(patient_path,file))
        files = [i for i in os.listdir(patient_path) if i.endswith('.dcm') and not i.startswith('RTPLAN')]
        for file in files:
            found = False
            for key in plan_keys:
                if file.find(key) != -1:
                    self.patient_folders[MRN][key].append(os.path.join(patient_path,file))
                    found = True
                    break
            if not found:
                print('Had an issue here with {} at {}'.format(file, patient_path))

    def depricated(self, patient_path):
        files = [i for i in os.listdir(patient_path) if i.endswith('.dcm')]
        reader = sitk.ImageFileReader()
        reader.LoadPrivateTagsOn()
        for file in files:
            if file.startswith('RTPLAN'):
                ext = 'RTPLAN'
            elif file.startswith('RTSTRUCT'):
                ext = 'RTSTRUCT'
            else:
                ext = 'RTDOSE'
            if ext != 'RTDOSE':
                ds = pydicom.read_file(os.path.join(patient_path,file))
                MRN = ds.PatientID
                if ext == 'RTPLAN':
                    referencedSOPInstanceUID = ds.ReferencedStudySequence[0].ReferencedSOPInstanceUID
                else:
                    referencedSOPInstanceUID = ds.ReferencedStudySequence[0].ReferencedSOPInstanceUID
            else:
                reader.SetFileName(os.path.join(patient_path,file))
                reader.ReadImageInformation()
                MRN = reader.GetMetaData("0010|0020")
                referencedSOPInstanceUID = reader.GetMetaData("0020|000e")
            if MRN not in self.patient_folders:
                self.patient_folders[MRN] = {}
            if referencedSOPInstanceUID not in self.patient_folders[MRN]:
                self.patient_folders[MRN][referencedSOPInstanceUID] = {'RTPLAN':[],'RTSTRUCT':[],'RTDOSE':[]}
            self.patient_folders[MRN][referencedSOPInstanceUID][ext].append(file)

    def combine_plan_RTs(self, MRN):
        for plan in self.patient_folders[MRN].keys():
            files = self.patient_folders[MRN][plan]
            out_path = os.path.join(self.out_path,MRN,plan)
            if files:
                if not os.path.exists(out_path):
                    os.makedirs(out_path)
                if not os.path.exists(os.path.join(out_path,'StudyInstanceUID.txt')):
                    ds = pydicom.read_file(files[0])
                    fid = open(os.path.join(out_path,'StudyInstanceUID.txt'),'w+')
                    fid.write(ds.StudyInstanceUID)
                    fid.close()
            for file in files:
                if not os.path.exists(os.path.join(out_path,os.path.split(file)[-1])):
                    shutil.copy2(file,os.path.join(out_path,os.path.split(file)[-1]))
            xxx = 1


if __name__ == '__main__':
    pass

