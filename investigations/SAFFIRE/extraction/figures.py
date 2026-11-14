from __future__ import annotations
import os
os.environ.setdefault("MPLCONFIGDIR", "/tmp/saffire-matplotlib")
import re
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw
from extraction.common import RAW, PROCESSED, read_csv, write_csv, source_path


def run():
    out=PROCESSED/"figures";out.mkdir(exist_ok=True)
    groups=defaultdict(list)
    for row in read_csv(PROCESSED/"sensor_timeseries.csv"):
        groups[row["test_id"]].append(row)
    fig,axes=plt.subplots(3,3,figsize=(13,9),sharex=True)
    for ax,(test,rows) in zip(axes.flat,sorted(groups.items())):
        t=np.array([float(r["time_since_ignition_s"]) for r in rows]);c=np.array([float(r["co2_ppm"]) for r in rows])
        base=np.median(c[(t>=-30)&(t<0)])
        visible=(t>=-30)&(t<=185)
        ax.plot(t[visible],c[visible]-base,lw=1);ax.axvspan(-30,0,color="gray",alpha=.15);ax.axvspan(150,180,color="orange",alpha=.2)
        ax.axvline(0,color="black",lw=.7);ax.axhline(0,color="gray",lw=.5);ax.set(title=test,xlim=(-30,185),ylabel="CO₂ change (ppm)",xlabel="Seconds from electrical ignition")
    fig.suptitle("Fixed-window response; shaded windows define target (not an exposure limit)")
    fig.tight_layout();fig.savefig(out/"co2_fixed_windows.png",dpi=140);plt.close(fig)
    fig,axes=plt.subplots(3,3,figsize=(13,9),sharex=False)
    for ax,(test,rows) in zip(axes.flat,sorted(groups.items())):
        t=np.array([float(r["time_since_ignition_s"]) for r in rows])
        plume=np.array([[float(r[f"plume_tc_{j}_c"]) for r in rows] for j in range(1,7)])
        ax.plot(t,plume.max(axis=0),label="max plume TC");ax.plot(t,[float(r["inlet_temperature_c"]) for r in rows],label="inlet")
        ax.set(title=test,ylabel="°C",xlabel="Seconds from ignition");ax.legend(fontsize=6)
    fig.suptitle("Sensor coverage differs by sample; these are local temperatures")
    fig.tight_layout();fig.savefig(out/"temperature_quality_control.png",dpi=140);plt.close(fig)
    metrics={(r["test_id"],r["metric"]):r["value"] for r in read_csv(PROCESSED/"metrics.csv")}
    fig,ax=plt.subplots(figsize=(6,4))
    ax.scatter([float(metrics[(f"II-{i}","flow_pre_cm_s")]) for i in (5,6)], [2.1,2.6])
    for i in (5,6):ax.annotate(f"II-{i}",(float(metrics[(f"II-{i}","flow_pre_cm_s")]),float(metrics[(f"II-{i}","spread_rate_reported_mm_s")])))
    ax.set(xlabel="Measured pre-ignition flow (cm/s)",ylabel="Published spread rate (mm/s)",title="Two SIBAL tests: descriptive comparison, n=2")
    fig.tight_layout();fig.savefig(out/"sibal_published_rates.png",dpi=140);plt.close(fig)
    sample_images(metrics,out)


def sample_images(metrics,out):
    candidates=defaultdict(list)
    for path in sorted(RAW.rglob("*.zip")):
        name=path.name
        match=re.search(r"S([1-9])C([12])",name)
        if not match or "Image_Data" not in name or "(2)" in name or "icmad" in name.lower():
            continue
        sample,camera=map(int,match.groups())
        preferred=2 if sample<=3 else 1
        if camera!=preferred:continue
        with ZipFile(path) as z:
            for info in z.infolist():
                m=re.search(r"S[1-9]C[12]-(\d{13})",info.filename)
                extension=Path(info.filename).suffix.lower()
                if m and extension in (".jpeg",".jpg",".tif",".tiff") and not info.filename.startswith("__MACOSX"):
                    priority=0 if "Mapped" in name and extension in (".jpeg",".jpg") else 1 if "Mapped" in name else 2
                    candidates[sample].append((priority,int(m.group(1)),path,info.filename))
    canvas=Image.new("RGB",(1050,9*150),"#151515")
    audit=[]
    for i in range(1,10):
        t0=float(metrics[(f"II-{i}","ignition_epoch_ms")])
        if not candidates[i]:continue
        for col,offset in enumerate([30,90,150]):
            near=[r for r in candidates[i] if abs(r[1]-(t0+offset*1000))<=2000]
            if near:
                priority,epoch,path,member=min(near,key=lambda r:(r[0],abs(r[1]-(t0+offset*1000)),r[2].name,r[3]))
            else:
                priority,epoch,path,member=min(candidates[i],key=lambda r:(abs(r[1]-(t0+offset*1000)),r[0],r[2].name,r[3]))
            with ZipFile(path) as z:
                with z.open(member) as handle:
                    im=Image.open(handle).convert("RGB")
            im.thumbnail((340,110))
            x,y=col*350,(i-1)*150
            canvas.paste(im,(x+(350-im.width)//2,y+28))
            ImageDraw.Draw(canvas).text((x+5,y+5),f"II-{i}: {(epoch-t0)/1000:.1f} s",fill="white")
            audit.append({"test_id":f"II-{i}","requested_time_s":offset,"actual_time_s":round((epoch-t0)/1000,3),"time_mismatch_s":round(abs((epoch-t0)/1000-offset),3),"source_file":source_path(path),"archive_member":member,"method":"prefer_mapped_JPEG_then_TIFF_within2s_else_nearest_unmapped; preferred_camera; visual_QC_only"})
    canvas.save(out/"image_contact_sheet.jpg",quality=90)
    write_csv(PROCESSED/"image_frame_audit.csv",audit)
