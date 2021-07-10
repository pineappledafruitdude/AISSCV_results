from pathlib import Path
import pandas as pd
import argparse
import os

from pandas.core.reshape.concat import concat


def combine_all_runs(folder:Path):
    output_dir = Path(folder,"excel")
    if not output_dir.exists():
        os.mkdir(output_dir)
    p = Path(folder).absolute().glob('**/*')
    runs = [x for x in p if x.is_dir() and x.name.startswith("run_")]
    all_total_results = pd.DataFrame()
    all_class_results_ap = pd.DataFrame()
    all_class_results_tp = pd.DataFrame()
    all_class_results_fp = pd.DataFrame()
    all_class_results_list:list[pd.DataFrame] = []
    for run in runs:
        result_txt = Path(run).absolute().glob('**/result*.txt').__next__()
        if not result_txt:
            raise Exception("%s has no results.txt or result.txt" % (run.name))
        class_output, total_output = read_results(result_txt, output_dir)
        total_output["run"] = run.name
        if len(all_total_results.index) == 0:
            all_total_results = total_output
        else:
            print("concat")
            all_total_results = pd.concat([all_total_results, total_output])
        
        all_class_results_list.append(class_output)
    

    all_total_results.set_index("run").sort_index().to_excel(Path(output_dir, folder.name+"_all_runs.xlsx"))

    for cls in all_class_results_list:

        if len(all_class_results_ap.index) == 0:
            all_class_results_ap = cls[["class","AP"]].set_index(["class"]).sort_index()
        else:
            all_class_results_ap = pd.concat([all_class_results_ap, cls[["class","AP"]].set_index(["class"])], axis=1)
        
        if len(all_class_results_tp.index) == 0:
            all_class_results_tp = cls[["class","TP"]].set_index(["class"]).sort_index()
        else:
            all_class_results_tp = pd.concat([all_class_results_tp, cls[["class","TP"]].set_index(["class"])], axis=1)
        
        if len(all_class_results_fp.index) == 0:
            all_class_results_fp = cls[["class","FP"]].set_index(["class"]).sort_index()
        else:
            all_class_results_fp = pd.concat([all_class_results_fp, cls[["class","FP"]].set_index(["class"])], axis=1)
    all_class_results_ap['AP(mean)'] = all_class_results_ap.mean(axis=1)
    all_class_results_tp['TP(mean)'] = all_class_results_tp.mean(axis=1)
    all_class_results_fp['FP(mean)'] = all_class_results_fp.mean(axis=1)
    final_result = pd.concat([all_class_results_ap[['AP(mean)']], all_class_results_tp[['TP(mean)']], all_class_results_fp[['FP(mean)']]], axis=1)
    final_result.to_excel(Path(output_dir, folder.name+"_all_runs_classes.xlsx"))

def read_results(file_path: Path, output_dir:Path):
    run_name = file_path.absolute().parent
    class_output = pd.DataFrame(
        columns=["class", "AP", "TP", "FP"])
    total_output = pd.DataFrame(
        columns=["treshold", "precision", "recall", "f1", "TP", "FP", "FN", "average IoU", "mAP"])
    content: list[str] = []
    precision_line = None
    total_tp_line = None
    map_line = None
    with open(file_path, 'rt') as myfile:
        for line in myfile:
            parsed_line = line.strip().replace(' ', '')
            if parsed_line.startswith("class_id") or parsed_line.startswith("forconf_thresh") or parsed_line.startswith("meanaverageprecision"):
                content.append(parsed_line)

    for element in content:
        data = element.split("=")
        if data[0] == "class_id":
            parsed_class = parse_class(data)
            class_output.loc[len(class_output)] = parsed_class
        elif data[0] == "forconf_thresh":
            if data[1].split(",")[1] == "precision":
                precision_line = parse_precision_line(data)
            else:
                total_tp_line = parse_tp_line(data)
        elif data[0] == "meanaverageprecision(mAP@0.50)":
            map_line = parse_map(data)

    # combine
    row = precision_line + total_tp_line + map_line
    total_output.loc[len(total_output)] = row

    class_output.set_index("class").to_excel(Path(output_dir, str(run_name.name)+"_class_results.xlsx") )

    return class_output, total_output



def parse_class(data: str):
    class_name = data[2].split(",")[0]
    ap = round(float(data[3].split("\t")[0].split('%')[0])/100,4)
    tp = int(data[4].split(",")[0])
    fp = int(data[5].split(")")[0])
    # print("Class: %s, AP: %s, TP: %s, FP %s" % (class_name, ap, tp, fp))
    return [class_name, ap, tp, fp]


def parse_precision_line(data: str):
    treshold = float(data[1].split(",")[0])
    precision = float(data[2].split(",")[0])
    recall = float(data[3].split(",")[0])
    f1 = float(data[4])
    # print("Treshold: %s, Precision: %s, Recall: %s, F1 %s" %
    #       (treshold, precision, recall, f1))
    return [treshold, precision, recall, f1]


def parse_tp_line(data: str):
    tp = int(data[2].split(",")[0])
    fp = int(data[3].split(",")[0])
    fn = int(data[4].split(",")[0])
    average_iou = float(round(float(data[5].split("%")[0])/100, 4))
    # print("Total TP: %s, Total FP: %s, Total FN: %s, Average IoU: %s" %
    #       (tp, fp, fn, average_iou))
    return [tp, fp, fn, average_iou]


def parse_map(data: str):

    map = data[1].split(",")[0]
    # print("Map %s" % map)
    return [map]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Parse results.txt into excel files')
    parser.add_argument('-f', metavar='results.txt file path', type=str, required=True,
                        help='Results.txt file path')
    args = parser.parse_args()
    combine_all_runs(Path(args.f))
