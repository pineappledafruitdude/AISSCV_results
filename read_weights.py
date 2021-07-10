from pathlib import Path
import pandas as pd
import argparse


def read_results(file_path: Path):
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

    class_output.set_index("class").to_excel(
        str(run_name)+"_class_results.xlsx")
    total_output.to_excel(str(run_name)+"_total_results.xlsx")


def parse_class(data: str):
    class_name = data[2].split(",")[0]
    ap = data[3].split("\t")[0]
    tp = data[4].split(",")[0]
    fp = data[5].split(")")[0]
    # print("Class: %s, AP: %s, TP: %s, FP %s" % (class_name, ap, tp, fp))
    return [class_name, ap, tp, fp]


def parse_precision_line(data: str):
    treshold = data[1].split(",")[0]
    precision = data[2].split(",")[0]
    recall = data[3].split(",")[0]
    f1 = data[4]
    # print("Treshold: %s, Precision: %s, Recall: %s, F1 %s" %
    #       (treshold, precision, recall, f1))
    return [treshold, precision, recall, f1]


def parse_tp_line(data: str):
    tp = data[2].split(",")[0]
    fp = data[3].split(",")[0]
    fn = data[4].split(",")[0]
    average_iou = round(float(data[5].split("%")[0])/100, 4)
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
    read_results(Path(args.f))
