__author__ = 'Brian M Anderson'
# Created on 5/19/2020

from connect import *
import clr
clr.AddReference('System.Windows.Forms')
import os


class import_dicom_class:
    def __init__(self):
        try:
            self.patient = get_current('Patient')
            self.patient_id = self.patient.PatientID
            self.case = get_current('Case')
        except:
            self.patient_id = '0'
        self.patient_db = get_current("PatientDB")

    def import_dicoms_new(self, MRN, path):
        patient_path = os.path.join(path,MRN)
        for plan in os.listdir(patient_path):
            plan_path = os.path.join(patient_path,plan)
            if not os.path.exists(os.path.join(plan_path, 'StudyInstanceUID.txt')):
                print('Need to create a StudyInstanceUID.txt file!')
                continue
            if os.path.exists(os.path.join(plan_path,'Imported.txt')):
                print('Already done')
                continue
            fid = open(os.path.join(plan_path, 'StudyInstanceUID.txt'))
            study_instance_uid = fid.readline()
            fid.close()
            print('importing dicom')
            info_all = self.patient_db.QueryPatientInfo(Filter={"PatientID": MRN})
            # If it isn't, see if it's in the secondary database
            if not info_all:
                info_all = self.patient_db.QueryPatientInfo(Filter={"PatientID": MRN}, UseIndexService=True)
            info = []
            for info_temp in info_all:
                if info_temp['PatientID'] == MRN:
                    info = info_temp
                    break
            pi_all = self.patient_db.QueryPatientsFromRepositoryByAETitle(AETitle='EVERCORE_SCP', SearchCriterias={'PatientID': MRN})
            pi = {}
            for pi_temp in pi_all:
                if pi_temp['PatientID'] == MRN:
                    pi = pi_temp
                    break
            pi['StudyInstanceUID'] = study_instance_uid
            studies = self.patient_db.QueryStudiesFromRepositoryByAETitle(AETitle='EVERCORE_SCP', SearchCriterias=pi)
            series = []
            for study in studies:
                series += self.patient_db.QuerySeriesFromRepositoryByAETitle(AETitle='EVERCORE_SCP',SearchCriterias=study)
            if not info:
                for seri in series:
                    try:
                        self.patient_db.ImportPatientFromRepositoryByAETitle(AETitle='EVERCORE_SCP', SeriesOrInstances=[seri])
                        break
                    except:
                        continue
                self.patient_db = get_current("PatientDB")  # Got a new patient, update the patient db
                self.patient_id = MRN
                self.patient = get_current("Patient")
                self.case = get_current("Case")
                self.case.CaseName = plan
                self.patient.Save()
            print('info found')
            if self.patient_id != MRN:
                print('patient id does not match MRN')
                if self.patient_id != '0':
                    self.patient.Save()
                print(info)
                self.patient = self.patient_db.LoadPatient(PatientInfo=info, AllowPatientUpgrade=True)
                self.patient_id = self.patient.PatientID
            case_names = [case.CaseName for case in self.patient.Cases]
            imported_uids = []
            if plan in case_names:
                self.case = self.patient.Cases[case_names.index(plan)]
                imported_uids = [e.Series[0].ImportedDicomUID for e in self.case.Examinations]
            import_series = [i for i in series if i['SeriesInstanceUID'] not in imported_uids]
            if import_series:
                for series in import_series:
                    if series['Modality'] != 'CT' and series['Modality'] != 'MR':
                        continue
                    case_names = [case.CaseName for case in self.patient.Cases]
                    try:
                        if plan in case_names:
                            self.patient.ImportDataFromRepositoryByAETitle(AETitle='EVERCORE_SCP', SeriesOrInstances=[series], CaseName=plan)
                            self.patient.Save()
                        else:
                            self.patient.ImportDataFromRepositoryByAETitle(AETitle='EVERCORE_SCP', SeriesOrInstances=[series], CaseName=None)
                            self.patient.Save()
                            for case in self.patient.Cases:
                                if case.CaseName not in case_names: # This is the new one!
                                    case.CaseName = plan
                                    self.patient.Save()
                                    break
                    except:
                        print('failed importing')
                        print(series)
            pi_all = self.patient_db.QueryPatientsFromPath(Path=plan_path, SearchCriterias={'PatientID': MRN})
            pi = {}
            for pi_temp in pi_all:
                if pi_temp['PatientID'] == MRN:
                    pi = pi_temp
                    break
            studies = self.patient_db.QueryStudiesFromPath(Path=plan_path, SearchCriterias=pi)
            series = []
            for study in studies:
                series += self.patient_db.QuerySeriesFromPath(Path=plan_path,
                                                              SearchCriterias=study)
            self.patient.ImportDataFromPath(Path=plan_path, SeriesOrInstances=series, CaseName=plan)
            self.patient.Save()
            fid = open(os.path.join(plan_path,'Imported.txt'),'w+')
            fid.close()
        return None

def main():
    path = r'Y:\Exports'
    print('running')
    import_class = import_dicom_class()
    for MRN in os.listdir(path):
        try:
            import_class.import_dicoms_new(MRN, path)
        except:
            import_class.patient_id = '0'
            continue


if __name__ == "__main__":
    main()
