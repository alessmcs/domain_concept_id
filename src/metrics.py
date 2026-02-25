# Using pandas & numpy & dataframes, compile the results for each case study 
import csv
import json
import pandas as pd
import numpy as np

def get_key_from_value(d, val):
    for key, value in d.items():
        if value == val:
            return key
    return None

def combine_outputs(output1, output2, name_dict):
    domain = [get_key_from_value(name_dict, c) for c in output2["Domain-specific"]] # most accurate bc it's the 2nd pass
    implementation = [get_key_from_value(name_dict, c) for c in output1["Implementation detail"] + output2["Implementation detail"]]

    return domain, implementation

def compare(labels, output, results_file, iter_no):
    """
    Compare the labels with the output and write the results to a CSV file.

    Note: 
    TP : name is in labels and output
    FP : name is in output but not in labels
    FN : name is in labels but not in output
    TN : name is not in labels and not in output

    Params: 
    labels: dict 
    output: dict
    results_file: str (path to the CSV file with the results)

    Returns: 
    Average precision? 
    """

    # Init the csv file if it doesn't exist
    with open(results_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # Check if the file is empty
            writer.writerow(['dateTime', 'iteration#', 'class_precision', 'method_precision', 'attr_precision', 'avg_precision'])

    # Class precision

    expected_classes = labels["classes"]
    output_classes = output["classes"]
    
    labels_class_names = set(expected_classes.keys())
    output_class_names = set(output_classes.keys())
    
    # Calculate metrics
    tp_classes = labels_class_names & output_class_names
    fp_classes = output_class_names - labels_class_names
    fn_classes = labels_class_names - output_class_names

    tp_count = len(tp_classes)
    fp_count = len(fp_classes)
    
    # Calculate precision and recall
    precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0
    class_precision = tp_count / (tp_count + fp_count) if (tp_count + fp_count) > 0 else 0

    # Attribute precision
    attr_precision = []
    method_precision = []

    for label_class in labels_class_names:
        if label_class in output_class_names:
            # For attributes - now this works
            label_attrs = set(expected_classes[label_class]["Attributes"])
            output_attrs = set(output_classes[label_class]["Attributes"])
            
            tp_attrs = label_attrs & output_attrs  # Intersection: in both
            fp_attrs = output_attrs - label_attrs  # In output but not in labels
            
            tp_count_attr = len(tp_attrs)
            fp_count_attr = len(fp_attrs)

            precision_attr = tp_count_attr / (tp_count_attr + fp_count_attr) if (tp_count_attr + fp_count_attr) > 0 else 0
            attr_precision.append(precision_attr)

            # For methods
            label_methods = set(expected_classes[label_class]["Methods"])
            output_methods = set(output_classes[label_class]["Methods"])
            tp_methods = label_methods & output_methods  # Intersection: in both
            fp_methods = output_methods - label_methods  # In output but not in labels

            tp_count_methods = len(tp_methods)
            fp_count_methods = len(fp_methods)

            precision_methods = tp_count_methods / (tp_count_methods + fp_count_methods) if (tp_count_methods + fp_count_methods) > 0 else 0
            method_precision.append(precision_methods)
            
    avg_attr_precision = np.mean(attr_precision) if attr_precision else 0
    avg_method_precision = np.mean(method_precision) if method_precision else 0

    print(f"Class precision: {class_precision})")
    print(f"Attribute precisions: {attr_precision}), avg: {avg_attr_precision}")
    print(f"Method precisions: {method_precision}), avg: {avg_method_precision}")

     # Compute for associations as well 
    expected_associations = labels["associations"]

    if len(expected_associations) > 0:

        output_associations = output.get("associations", [])

        assos_tp_count = 0
        assos_fp_count = 0
        assos_precision = 0

        for assoc in output_associations: 
            if [assoc[0], assoc[1]] in expected_associations or [assoc[1], assoc[0]] in expected_associations:
                assos_tp_count += 1
            elif [assoc[0], assoc[1]] not in expected_associations:
                assos_fp_count += 1
        
        assos_precision = assos_tp_count / (assos_tp_count + assos_fp_count) if (assos_tp_count + assos_fp_count) > 0 else 0


        print(f"Association precision: {assos_precision}")

        # Compute total average precision
        total_avg_precision = np.mean([class_precision, avg_attr_precision, avg_method_precision, assos_precision])
        print(f"Total average precision: {total_avg_precision}")
    else:
    # Compute total average precision
        total_avg_precision = np.mean([class_precision, avg_attr_precision, avg_method_precision])
        print(f"Total average precision: {total_avg_precision}")

    # Write results to CSV
    with open(results_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([pd.Timestamp.now(), iter_no, class_precision, avg_method_precision, avg_attr_precision, total_avg_precision])

    return total_avg_precision

def compare_ump(gt, output, results_file, iter_no):
    # gt is the uml file that we're comparing it to (ground truth)

    with open(results_file, 'a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:  # Check if the file is empty
            writer.writerow(['dateTime', 'iteration#', 'class_precision', 'method_precision', 'attr_precision', 'avg_precision'])

    expected_classes = gt["classes"]
    output_classes = output["classes"]

    expected_class_names = set(expected_classes.keys())
    output_class_names = set(output_classes.keys())

    # Compute class precision
    tp_classes = expected_class_names & output_class_names
    fp_classes = output_class_names - expected_class_names
    fn_classes = expected_class_names - output_class_names  

    class_precision = len(tp_classes) / (len(tp_classes) + len(fp_classes)) if (len(tp_classes) + len(fp_classes)) > 0 else 0
    
    # Attribute precision 
    attr_precision = []
    method_precision = []

    for ec in expected_class_names:
        if ec in output_class_names:
            expected_attrs = set(expected_classes[ec]["attributes"])
            output_attrs = set(output_classes[ec]["attributes"])

            tp_attrs = expected_attrs & output_attrs
            fp_attrs = output_attrs - expected_attrs

            precision_attr = len(tp_attrs) / (len(tp_attrs) + len(fp_attrs)) if (len(tp_attrs) + len(fp_attrs)) > 0 else 0
            attr_precision.append(precision_attr)

            # Method precision
            expected_methods = set(expected_classes[ec]["methods"])
            output_methods = set(output_classes[ec]["methods"])

            tp_methods = expected_methods & output_methods
            fp_methods = output_methods - expected_methods

            precision_method = len(tp_methods) / (len(tp_methods) + len(fp_methods)) if (len(tp_methods) + len(fp_methods)) > 0 else 0
            method_precision.append(precision_method)



    return class_precision, np.mean(attr_precision) if attr_precision else 0, np.mean(method_precision) if method_precision else 0






# Previous comparison function - deprecated
# def compare(output1, output2, csv_file, name_dict):
#     df = pd.read_csv(csv_file, header=0) 

#     # class_names = [s.strip() for s in df.columns.tolist()[2:]]
#     # actual = [s.strip() for s in (df.iloc[0].tolist())[2:]]

#     class_names = [s for s in df.columns.tolist()[2:]]
#     actual = df.iloc[0]

#     print(f"DF Length: {len(df)}")

#     domain, implementation = combine_outputs(output1, output2, name_dict)

#     tp = []
#     fp = []
#     fn = []
#     tn = []

#     new_row = pd.Series({col: None for col in df.columns})

#     new_row = {}

#     new_row['precision'] = 0
#     new_row['recall'] = 0

#     for c in class_names:
#         if c in domain:
#             new_row[c] = 'D'
#             if actual[c] == 'D':
#                 tp.append(c)
#             else:
#                 fp.append(c)
#         elif c in implementation:
#             new_row[c] = 'I'
#             if actual[c] == 'I':
#                 tn.append(c)
#             else:
#                 fn.append(c)

#     new_row['precision'] = len(tp) / (len(tp) + len(fp)) if (len(tp) + len(fp)) > 0 else 0
#     new_row['recall'] = len(tp) / (len(tp) + len(fn)) if (len(tp) + len(fn)) > 0 else 0    

#     new_df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
#     new_df.to_csv(csv_file, index=False)

#     # calc averages
#     avg_precision = new_df['precision'].mean()
#     avg_recall = new_df['recall'].mean()

#     return avg_precision, avg_recall

if __name__ == "__main__":

    # with open("/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/project_output.json", "r") as output1_file:
    #         output1 = json.load(output1_file)

    # with open("/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/project_output2.json", "r") as output2_file:
    #         output2 = json.load(output2_file)

    # compare(output1["classifications"], output2["classifications"], 
    #         "/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data/HealthPlus_data/metrics.csv",
    #         output1["tokenized_class_names"])
    
    with open("/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data/Espresso/labels.json", "r", encoding="utf-8") as f:
        labels_dict = json.load(f)

    mo = {'classes': {'SettingsFragment': {'Attributes': ['prefStartTime', 'prefsEndTime', 'prefAlert', 'prefNotificationInterval', 'prefNavigationBar', 'sp', 'startHour', 'startMinute', 'endHour', 'endMinute'], 'Methods': ['onCreatePreferences', 'initPrefs']}, 'AboutFragment': {'Attributes': ['prefRate', 'prefLicenses', 'prefThx1', 'prefThx2', 'prefSourceCode', 'prefSendAdvices', 'prefDonate', 'prefVersion'], 'Methods': ['onCreatePreferences', 'initPrefs']}, 'OnboardingActivity': {'Attributes': ['viewPager', 'buttonFinish', 'buttonPre', 'buttonNext', 'indicators', 'bgColors', 'currentPosition', 'MSG_DATA_INSERT_FINISH', 'handler'], 'Methods': ['onCreate', 'initViews', 'initData', 'updateIndicators', 'enableShortcuts', 'navigateToMainActivity']}, 'OnboardingFragment': {'Attributes': ['sectionLabel', 'sectionIntro', 'sectionImg', 'page', 'ARG_SECTION_NUMBER'], 'Methods': ['newInstance', 'onCreate', 'onCreateView', 'initViews']}, 'CompanyDetailFragment': {'Attributes': ['fab', 'textViewCompanyName', 'textViewTel', 'textViewWebsite', 'presenter', 'tel', 'website'], 'Methods': ['newInstance', 'onCreate', 'onCreateView', 'onResume', 'onPause', 'onOptionsItemSelected', 'initViews', 'setCompanyName', 'setCompanyTel', 'setCompanyWebsite', 'showErrorMsg', 'share']}, 'CompanyDetailContract': {'Attributes': [], 'Methods': []}, 'CompanyDetailActivity': {'Attributes': ['fragment', 'COMPANY_ID'], 'Methods': ['onCreate', 'onSaveInstanceState']}, 'SearchFragment': {'Attributes': ['searchView', 'recyclerView', 'adapter', 'presenter'], 'Methods': ['newInstance', 'onCreate', 'onCreateView', 'onResume', 'onPause', 'onOptionsItemSelected', 'initViews', 'showResult', 'hideImm']}, 'SearchActivity': {'Attributes': ['fragment'], 'Methods': ['onCreate', 'onSaveInstanceState']}, 'PackageFilterType': {'Attributes': [], 'Methods': []}, 'PackagesContract': {'Attributes': [], 'Methods': []}, 'PackagesFragment': {'Attributes': ['bottomNavigationView', 'fab', 'recyclerView', 'emptyView', 'refreshLayout', 'adapter', 'presenter', 'selectedPackageNumber'], 'Methods': ['newInstance', 'onCreate', 'onCreateView', 'onResume', 'onPause', 'onCreateOptionsMenu', 'onOptionsItemSelected', 'onContextItemSelected', 'initViews', 'setLoadingIndicator', 'showEmptyView', 'showPackages', 'shareTo', 'showPackageRemovedMsg', 'copyPackageNumber', 'showNetworkError', 'setSelectedPackage']}, 'PackageDetailsFragment': {'Attributes': ['recyclerView', 'fab', 'swipeRefreshLayout', 'toolbarLayout', 'adapter', 'presenter'], 'Methods': ['newInstance', 'onCreate', 'onCreateView', 'onResume', 'onPause', 'onDestroy', 'onCreateOptionsMenu', 'onOptionsItemSelected', 'initViews', 'setLoadingIndicator', 'showNetworkError', 'showPackageDetails', 'setToolbarBackground', 'shareTo', 'copyPackageNumber', 'showDeleteAlertDialog', 'showEditNameDialog', 'showInputIsEmpty']}, 'PackageDetailsContract': {'Attributes': [], 'Methods': []}, 'CompaniesFragment': {'Attributes': ['recyclerView', 'presenter', 'adapter'], 'Methods': ['newInstance', 'onCreate', 'onCreateView', 'onResume', 'onPause', 'onCreateOptionsMenu', 'onOptionsItemSelected', 'initViews', 'showGetCompaniesError', 'showCompanies']}, 'CompaniesAdapter': {'Attributes': ['context', 'inflater', 'list', 'listener', 'TYPE_NORMAL', 'TYPE_WITH_HEADER'], 'Methods': []}, 'CompaniesContract': {'Attributes': [], 'Methods': []}, 'FastScrollRecyclerView': {'Attributes': ['mScrollbar', 'mScrollPosState', 'mDownX', 'mDownY', 'mLastY', 'mStateChangeListener'], 'Methods': ['getScrollBarWidth', 'getScrollBarThumbHeight', 'onFinishInflate', 'onInterceptTouchEvent', 'onTouchEvent', 'handleTouchEvent', 'onRequestDisallowInterceptTouchEvent', 'getAvailableScrollHeight', 'getAvailableScrollBarHeight', 'draw', 'synchronizeScrollBarThumbOffsetToViewScroll', 'scrollToPositionAtProgress', 'onUpdateScrollbar', 'getCurScrollState', 'setThumbColor', 'setTrackColor', 'setPopupBgColor', 'setPopupTextColor', 'setPopupTextSize', 'setPopUpTypeface', 'setAutoHideDelay', 'setAutoHideEnabled', 'setStateChangeListener']}, 'Timeline': {'Attributes': ['lineSize', 'startLine', 'finishLine', 'atomDrawable'], 'Methods': ['init', 'onDraw', 'onMeasure', 'onSizeChanged', 'initDrawableSize']}, 'FastScroller': {'Attributes': ['DEFAULT_AUTO_HIDE_DELAY', 'mRecyclerView', 'mPopup', 'mThumbHeight', 'mWidth', 'mThumb', 'mTrack', 'mTmpRect', 'mInvalidateRect', 'mInvalidateTmpRect', 'mTouchInset', 'mTouchOffset', 'mThumbPosition', 'mOffset', 'mIsDragging', 'mAutoHideAnimator', 'mAnimatingShow', 'mAutoHideDelay', 'DEFAULT_AUTO_HIDE_DELAY', 'mAutoHideEnabled', 'mHideRunnable'], 'Methods': []}, 'Api': {'Attributes': ['API_BASE', 'PACKAGE_STATE', 'COMPANY_QUERY'], 'Methods': []}, 'ReminderService': {'Attributes': ['preference', 'compositeDisposable'], 'Methods': ['onCreate', 'onBind', 'onHandleIntent', 'onStartCommand', 'onDestroy', 'buildNotification', 'setNotifications', 'refreshPackage', 'pushNotification']}, 'CompanyRecognition': {'Attributes': ['companyCode', 'number', 'companyCode', 'id', 'noPre'], 'Methods': []}, 'Auto': {'Attributes': ['companyCode', 'id', 'noPre'], 'Methods': []}, 'Package': {'Attributes': ['STATUS_FAILED', 'STATUS_NORMAL', 'STATUS_ON_THE_WAY', 'STATUS_DELIVERED', 'STATUS_RETURNED', 'STATUS_RETURNING', 'STATUS_OTHER', 'message', 'number', 'condition', 'company', 'status', 'state', 'data', 'pushable', 'name', 'companyChineseName', 'timestamp'], 'Methods': []}, 'PackageWithCompany': {'Attributes': ['pkg', 'company'], 'Methods': []}, 'Company': {'Attributes': ['name', 'id', 'tel', 'website', 'alphabet', 'avatar'], 'Methods': []}, 'PackageStatus': {'Attributes': ['time', 'ftime', 'location'], 'Methods': []}, 'PackageAndCompanyPairs': {'Attributes': ['packages', 'companies'], 'Methods': []}, 'PackagesRepository': {'Attributes': ['INSTANCE', 'packagesRemoteDataSource', 'packagesLocalDataSource', 'cachedPackages'], 'Methods': ['getInstance', 'destroyInstance', 'getPackages', 'getPackage', 'savePackage', 'deletePackage', 'refreshPackages', 'refreshPackage', 'setAllPackagesRead', 'setPackageReadable', 'isPackageExist', 'updatePackageName', 'searchPackages', 'getPackageWithNumber', 'getPackageWithNumberFromLocalRepository']}, 'CompaniesDataSource': {'Attributes': [], 'Methods': ['getCompanies', 'getCompany', 'searchCompanies']}, 'CompaniesRepository': {'Attributes': ['INSTANCE', 'localDataSource'], 'Methods': ['getCompanies', 'getCompany', 'searchCompanies']}, 'PackagesDataSource': {'Attributes': [], 'Methods': []}, 'CompaniesLocalDataSource': {'Attributes': ['INSTANCE'], 'Methods': ['getInstance', 'getCompanies', 'getCompany', 'searchCompanies']}, 'PackagesLocalDataSource': {'Attributes': ['INSTANCE'], 'Methods': ['getInstance', 'destroyInstance', 'getPackages', 'getPackage', 'savePackage', 'deletePackage', 'refreshPackages', 'refreshPackage', 'setAllPackagesRead', 'setPackageReadable', 'isPackageExist', 'updatePackageName', 'searchPackages']}, 'PackagesRemoteDataSource': {'Attributes': [], 'Methods': ['getPackages', 'getPackage', 'savePackage', 'deletePackage', 'refreshPackages', 'refreshPackage', 'setAllPackagesRead', 'setPackageReadable', 'isPackageExist', 'updatePackageName', 'searchPackages']}, 'CaptureActivity': {'Attributes': ['cameraManager', 'handler', 'inactivityTimer', 'beepManager', 'scanPreview', 'scanContainer', 'scanCropView', 'scanLine', 'mCropRect', 'isHasSurface'], 'Methods': ['onCreate', 'onResume', 'onPause', 'onDestroy', 'onOptionsItemSelected', 'surfaceCreated', 'surfaceDestroyed', 'surfaceChanged', 'handleDecode', 'initCamera', 'restartPreviewAfterDelay', 'getCropRect', 'initCrop']}, 'OpenCameraInterface': {'Attributes': [], 'Methods': ['open']}}, 'associations': [['ReminderService', 'SettingsFragment'], ['OnboardingActivity', 'OnboardingFragment'], ['CompanyDetailContract', 'CompanyDetailFragment'], ['CompanyDetailActivity', 'CompanyDetailFragment'], ['CompaniesFragment', 'CompanyDetailFragment'], ['CompaniesAdapter', 'CompanyDetailFragment'], ['CompanyDetailFragment', 'Package'], ['CompanyDetailFragment', 'PackageWithCompany'], ['Company', 'CompanyDetailFragment'], ['CompanyDetailFragment', 'PackageAndCompanyPairs'], ['CompanyDetailFragment', 'PackagesRepository'], ['CompanyDetailFragment', 'PackagesDataSource'], ['CompanyDetailFragment', 'PackagesLocalDataSource'], ['CompanyDetailFragment', 'PackagesRemoteDataSource'], ['CompanyDetailActivity', 'CompanyDetailContract'], ['CompaniesFragment', 'CompanyDetailContract'], ['CompaniesAdapter', 'CompanyDetailContract'], ['CompanyDetailContract', 'Package'], ['CompanyDetailContract', 'PackageWithCompany'], ['Company', 'CompanyDetailContract'], ['CompanyDetailContract', 'PackageAndCompanyPairs'], ['CompanyDetailContract', 'PackagesRepository'], ['CompanyDetailContract', 'PackagesDataSource'], ['CompanyDetailContract', 'PackagesLocalDataSource'], ['CompanyDetailContract', 'PackagesRemoteDataSource'], ['CompanyDetailActivity', 'CompanyDetailActivity'], ['CompaniesFragment', 'CompanyDetailActivity'], ['CompaniesAdapter', 'CompanyDetailActivity'], ['CompanyDetailActivity', 'Package'], ['CompanyDetailActivity', 'PackageWithCompany'], ['Company', 'CompanyDetailActivity'], ['CompanyDetailActivity', 'PackageAndCompanyPairs'], ['CompanyDetailActivity', 'PackagesRepository'], ['CompanyDetailActivity', 'PackagesDataSource'], ['CompanyDetailActivity', 'PackagesLocalDataSource'], ['CompanyDetailActivity', 'PackagesRemoteDataSource'], ['SearchActivity', 'SearchFragment'], ['PackagesFragment', 'SearchFragment'], ['PackageDetailsFragment', 'SearchFragment'], ['PackageDetailsContract', 'SearchFragment'], ['CompanyRecognition', 'SearchFragment'], ['Auto', 'SearchFragment'], ['Package', 'SearchFragment'], ['PackageWithCompany', 'SearchFragment'], ['Company', 'SearchFragment'], ['PackageAndCompanyPairs', 'SearchFragment'], ['PackagesRepository', 'SearchFragment'], ['PackagesDataSource', 'SearchFragment'], ['PackagesLocalDataSource', 'SearchFragment'], ['PackagesRemoteDataSource', 'SearchFragment'], ['SearchActivity', 'SearchActivity'], ['PackagesFragment', 'SearchActivity'], ['PackageDetailsFragment', 'SearchActivity'], ['PackageDetailsContract', 'SearchActivity'], ['CompanyRecognition', 'SearchActivity'], ['Auto', 'SearchActivity'], ['Package', 'SearchActivity'], ['PackageWithCompany', 'SearchActivity'], ['Company', 'SearchActivity'], ['PackageAndCompanyPairs', 'SearchActivity'], ['PackagesRepository', 'SearchActivity'], ['PackagesDataSource', 'SearchActivity'], ['PackagesLocalDataSource', 'SearchActivity'], ['PackagesRemoteDataSource', 'SearchActivity'], ['Package', 'PackageFilterType'], ['PackageFilterType', 'PackageWithCompany'], ['Company', 'PackageFilterType'], ['PackageAndCompanyPairs', 'PackageFilterType'], ['PackageFilterType', 'PackagesRepository'], ['PackageFilterType', 'PackagesDataSource'], ['PackageFilterType', 'PackagesLocalDataSource'], ['PackageFilterType', 'PackagesRemoteDataSource'], ['PackagesContract', 'PackagesFragment'], ['PackageDetailsFragment', 'PackagesContract'], ['PackageDetailsContract', 'PackagesContract'], ['CompanyRecognition', 'PackagesContract'], ['Auto', 'PackagesContract'], ['Package', 'PackagesContract'], ['PackageWithCompany', 'PackagesContract'], ['Company', 'PackagesContract'], ['PackageAndCompanyPairs', 'PackagesContract'], ['PackagesContract', 'PackagesRepository'], ['PackagesContract', 'PackagesDataSource'], ['PackagesContract', 'PackagesLocalDataSource'], ['PackagesContract', 'PackagesRemoteDataSource'], ['PackageDetailsFragment', 'PackagesFragment'], ['PackageDetailsContract', 'PackagesFragment'], ['CompanyRecognition', 'PackagesFragment'], ['Auto', 'PackagesFragment'], ['Package', 'PackagesFragment'], ['PackageWithCompany', 'PackagesFragment'], ['Company', 'PackagesFragment'], ['PackageAndCompanyPairs', 'PackagesFragment'], ['PackagesFragment', 'PackagesRepository'], ['PackagesDataSource', 'PackagesFragment'], ['PackagesFragment', 'PackagesLocalDataSource'], ['PackagesFragment', 'PackagesRemoteDataSource'], ['PackageDetailsContract', 'PackageDetailsFragment'], ['CompanyRecognition', 'PackageDetailsFragment'], ['Auto', 'PackageDetailsFragment'], ['Package', 'PackageDetailsFragment'], ['PackageDetailsFragment', 'PackageWithCompany'], ['Company', 'PackageDetailsFragment'], ['PackageAndCompanyPairs', 'PackageDetailsFragment'], ['PackageDetailsFragment', 'PackagesRepository'], ['PackageDetailsFragment', 'PackagesDataSource'], ['PackageDetailsFragment', 'PackagesLocalDataSource'], ['PackageDetailsFragment', 'PackagesRemoteDataSource'], ['CompanyRecognition', 'PackageDetailsContract'], ['Auto', 'PackageDetailsContract'], ['Package', 'PackageDetailsContract'], ['PackageDetailsContract', 'PackageWithCompany'], ['Company', 'PackageDetailsContract'], ['PackageAndCompanyPairs', 'PackageDetailsContract'], ['PackageDetailsContract', 'PackagesRepository'], ['PackageDetailsContract', 'PackagesDataSource'], ['PackageDetailsContract', 'PackagesLocalDataSource'], ['PackageDetailsContract', 'PackagesRemoteDataSource'], ['CompaniesAdapter', 'CompaniesFragment'], ['CompaniesFragment', 'Company'], ['CompaniesFragment', 'PackageAndCompanyPairs'], ['CompaniesFragment', 'PackagesRepository'], ['CompaniesFragment', 'PackagesDataSource'], ['CompaniesFragment', 'PackagesLocalDataSource'], ['CompaniesFragment', 'PackagesRemoteDataSource'], ['CompaniesContract', 'CompanyRecognition'], ['Auto', 'CompaniesContract'], ['CompaniesContract', 'Package'], ['CompaniesContract', 'PackageWithCompany'], ['CompaniesContract', 'Company'], ['CompaniesContract', 'PackageAndCompanyPairs'], ['CompaniesContract', 'PackagesRepository'], ['CompaniesContract', 'PackagesDataSource'], ['CompaniesContract', 'PackagesLocalDataSource'], ['CompaniesContract', 'PackagesRemoteDataSource'], ['FastScrollRecyclerView', 'FastScroller'], ['FastScrollRecyclerView', 'FastScrollRecyclerView'], ['Package', 'Timeline'], ['PackageWithCompany', 'Timeline'], ['Company', 'Timeline'], ['PackageAndCompanyPairs', 'Timeline'], ['PackagesRepository', 'Timeline'], ['PackagesDataSource', 'Timeline'], ['PackagesLocalDataSource', 'Timeline'], ['PackagesRemoteDataSource', 'Timeline'], ['Api', 'Package'], ['Api', 'PackageWithCompany'], ['Api', 'Company'], ['Api', 'PackageAndCompanyPairs'], ['Api', 'PackagesRepository'], ['Api', 'PackagesDataSource'], ['Api', 'PackagesLocalDataSource'], ['Api', 'PackagesRemoteDataSource'], ['Auto', 'CompanyRecognition'], ['CompanyRecognition', 'Package'], ['CompanyRecognition', 'PackageWithCompany'], ['Company', 'CompanyRecognition'], ['CompanyRecognition', 'PackageAndCompanyPairs'], ['CompanyRecognition', 'PackagesRepository'], ['CompanyRecognition', 'PackagesDataSource'], ['CompanyRecognition', 'PackagesLocalDataSource'], ['CompanyRecognition', 'PackagesRemoteDataSource'], ['Auto', 'Package'], ['Auto', 'PackageWithCompany'], ['Auto', 'Company'], ['Auto', 'PackageAndCompanyPairs'], ['Auto', 'PackagesRepository'], ['Auto', 'PackagesDataSource'], ['Auto', 'PackagesLocalDataSource'], ['Auto', 'PackagesRemoteDataSource'], ['Package', 'PackageWithCompany'], ['PackageWithCompany', 'PackageWithCompany'], ['Company', 'PackageWithCompany'], ['PackageAndCompanyPairs', 'PackageWithCompany'], ['PackageWithCompany', 'PackagesRepository'], ['PackageWithCompany', 'PackagesDataSource'], ['PackageWithCompany', 'PackagesLocalDataSource'], ['PackageWithCompany', 'PackagesRemoteDataSource'], ['Package', 'PackageAndCompanyPairs'], ['Company', 'PackageAndCompanyPairs'], ['PackageAndCompanyPairs', 'PackageAndCompanyPairs'], ['PackageAndCompanyPairs', 'PackagesRepository'], ['PackageAndCompanyPairs', 'PackagesDataSource'], ['PackageAndCompanyPairs', 'PackagesLocalDataSource'], ['PackageAndCompanyPairs', 'PackagesRemoteDataSource'], ['PackagesRepository', 'PackagesRepository'], ['PackagesDataSource', 'PackagesRepository'], ['PackagesLocalDataSource', 'PackagesRepository'], ['PackagesRemoteDataSource', 'PackagesRepository'], ['CompaniesDataSource', 'CompaniesRepository'], ['CompaniesDataSource', 'PackagesDataSource'], ['CompaniesDataSource', 'PackagesLocalDataSource'], ['CompaniesDataSource', 'PackagesRemoteDataSource'], ['CompaniesRepository', 'CompaniesRepository'], ['CompaniesRepository', 'PackagesDataSource'], ['CompaniesRepository', 'PackagesLocalDataSource'], ['CompaniesRepository', 'PackagesRemoteDataSource'], ['CompaniesLocalDataSource', 'CompaniesLocalDataSource'], ['CompaniesLocalDataSource', 'PackagesLocalDataSource'], ['CompaniesLocalDataSource', 'PackagesRemoteDataSource'], ['PackagesLocalDataSource', 'PackagesLocalDataSource'], ['PackagesLocalDataSource', 'PackagesRemoteDataSource'], ['PackagesRemoteDataSource', 'PackagesRemoteDataSource']]}
    compare(labels_dict, mo, "/u/mancasat/Desktop/summer_intern/domain-concepts-identification-using-LLMs-aless/data/Espresso/metrics.csv",0)
