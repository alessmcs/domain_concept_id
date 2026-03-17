import json

p = input("Project name: ")

with open(f"../data_mcgill/{p}/ump_parsed.json") as f:
    keys1 = set(json.load(f)["classes"].keys())

with open(f"../data_mcgill/{p}/final_metrics_iter0.json") as f:
    keys2 = set(json.load(f)["classes"].keys())

TP = keys1 & keys2
FP = keys2 - keys1
FN = keys1 - keys2

print(f"TP: {len(TP)} {TP}")
print(f"FP: {len(FP)} {FP}")
print(f"FN: {len(FN)} {FN}")
print(f"Precision: {len(TP) / (len(TP) + len(FP)):.4f}")
# number of classes in GT
print(f"GT classes: {len(keys1)}")
print(f"Total generated: {len(keys2)}")