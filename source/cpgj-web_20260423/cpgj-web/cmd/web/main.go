package main

import (
	"embed"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

//go:embed static/index.html
var indexHTML embed.FS

var (
	baseDir     = "/data/uploads"
	previewPath = "/data/exports/indicator_preview.json"
	detailPath  = "/data/exports/indicator_detail_preview.json"
	maxBodySize int64 = 2 << 30
	categories        = map[string]string{
		"guide":     "01_指导书",
		"standard":  "02_标准文档",
		"history":   "03_历史测评记录_excel",
		"topology":  "04_拓扑与设备截图",
		"config":    "05_交换机与linux配置",
	}
	safeName = regexp.MustCompile(`[^\p{Han}\w.\-() ]+`)
)

type uploadResult struct {
	OK        bool     `json:"ok"`
	Category  string   `json:"category"`
	SavedPath string   `json:"saved_path"`
	Files     []string `json:"files"`
	Message   string   `json:"message"`
}

type fileItem struct {
	Name     string `json:"name"`
	RelPath  string `json:"rel_path"`
	Category string `json:"category"`
	Batch    string `json:"batch"`
	Size     int64  `json:"size"`
	ModTime  string `json:"mod_time"`
}

type filesResp struct {
	OK      bool       `json:"ok"`
	Files   []fileItem `json:"files,omitempty"`
	Message string     `json:"message"`
}

type deleteReq struct {
	RelPath string `json:"rel_path"`
}

type previewItem struct {
	Domain          string `json:"domain,omitempty"`
	Level2          string `json:"level2"`
	GeneralCount    int    `json:"general_count"`
	CloudCount      int    `json:"cloud_count"`
	MobileCount     int    `json:"mobile_count,omitempty"`
	IotCount        int    `json:"iot_count,omitempty"`
	IndustrialCount int    `json:"industrial_count,omitempty"`
	TotalCount      int    `json:"total_count"`
}

type previewResp struct {
	OK      bool          `json:"ok"`
	Items   []previewItem `json:"items,omitempty"`
	Message string        `json:"message"`
}

type previewDetailItem struct {
	ExtensionType string `json:"extension_type"`
	Domain        string `json:"domain,omitempty"`
	Level2        string `json:"level2"`
	Level3        string `json:"level3"`
}

type previewDetailResp struct {
	OK      bool                `json:"ok"`
	Items   []previewDetailItem `json:"items,omitempty"`
	Message string              `json:"message"`
}

type statsDomainRow struct {
	Domain          string `json:"domain"`
	GeneralCount    int    `json:"general_count"`
	CloudCount      int    `json:"cloud_count"`
	MobileCount     int    `json:"mobile_count"`
	IotCount        int    `json:"iot_count"`
	IndustrialCount int    `json:"industrial_count"`
	TotalCount      int    `json:"total_count"`
}

type statsL2Row struct {
	Domain          string `json:"domain"`
	Level2          string `json:"level2"`
	GeneralCount    int    `json:"general_count"`
	CloudCount      int    `json:"cloud_count"`
	MobileCount     int    `json:"mobile_count"`
	IotCount        int    `json:"iot_count"`
	IndustrialCount int    `json:"industrial_count"`
	TotalCount      int    `json:"total_count"`
}

type statsResp struct {
	OK            bool            `json:"ok"`
	L2ByDomain    []statsDomainRow `json:"l2_by_domain,omitempty"`
	L3ByDomain    []statsDomainRow `json:"l3_by_domain,omitempty"`
	L3ByDomainL2  []statsL2Row    `json:"l3_by_domain_l2,omitempty"`
	Message       string          `json:"message"`
}

func main() {
	if err := os.MkdirAll(baseDir, 0o755); err != nil {
		log.Fatalf("create base dir: %v", err)
	}
	if v := strings.TrimSpace(os.Getenv("PREVIEW_PATH")); v != "" {
		previewPath = v
	}
	if v := strings.TrimSpace(os.Getenv("DETAIL_PATH")); v != "" {
		detailPath = v
	}

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("ok"))
	})

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		b, err := indexHTML.ReadFile("static/index.html")
		if err != nil {
			http.Error(w, "页面加载失败", http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = w.Write(b)
	})

	http.HandleFunc("/upload", uploadHandler)
	http.HandleFunc("/files", filesHandler)
	http.HandleFunc("/preview", previewHandler)
	http.HandleFunc("/preview_detail", previewDetailHandler)
	http.HandleFunc("/stats", statsHandler)

	addr := ":8088"
	log.Printf("upload web started on %s", addr)
	if err := http.ListenAndServe(addr, nil); err != nil {
		log.Fatal(err)
	}
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "方法不允许", http.StatusMethodNotAllowed)
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, maxBodySize)
	if err := r.ParseMultipartForm(maxBodySize); err != nil {
		writeJSON(w, http.StatusBadRequest, uploadResult{OK: false, Message: "上传体积过大或格式错误"})
		return
	}

	catKey := strings.TrimSpace(r.FormValue("category"))
	catDir, ok := categories[catKey]
	if !ok {
		writeJSON(w, http.StatusBadRequest, uploadResult{OK: false, Message: "分类无效"})
		return
	}

	files := r.MultipartForm.File["files"]
	if len(files) == 0 {
		writeJSON(w, http.StatusBadRequest, uploadResult{OK: false, Message: "未选择文件"})
		return
	}

	batch := time.Now().Format("20060102_150405")
	dstDir := filepath.Join(baseDir, catDir, batch)
	if err := os.MkdirAll(dstDir, 0o755); err != nil {
		writeJSON(w, http.StatusInternalServerError, uploadResult{OK: false, Message: "创建目录失败"})
		return
	}

	saved := make([]string, 0, len(files))
	for _, fh := range files {
		name, err := saveOneFile(dstDir, fh)
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, uploadResult{OK: false, Message: "保存文件失败: " + err.Error()})
			return
		}
		saved = append(saved, name)
	}

	writeJSON(w, http.StatusOK, uploadResult{
		OK:        true,
		Category:  catDir,
		SavedPath: dstDir,
		Files:     saved,
		Message:   fmt.Sprintf("上传成功，共 %d 个文件", len(saved)),
	})
}

func filesHandler(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		items, err := listFiles()
		if err != nil {
			writeJSON(w, http.StatusInternalServerError, filesResp{OK: false, Message: "读取文件列表失败"})
			return
		}
		writeJSON(w, http.StatusOK, filesResp{OK: true, Files: items, Message: fmt.Sprintf("共 %d 个文件", len(items))})
	case http.MethodDelete:
		var req deleteReq
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			writeJSON(w, http.StatusBadRequest, filesResp{OK: false, Message: "参数格式错误"})
			return
		}
		if err := deleteFile(req.RelPath); err != nil {
			writeJSON(w, http.StatusBadRequest, filesResp{OK: false, Message: err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, filesResp{OK: true, Message: "删除成功"})
	default:
		http.Error(w, "方法不允许", http.StatusMethodNotAllowed)
	}
}

func previewHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "方法不允许", http.StatusMethodNotAllowed)
		return
	}
	items, err := listPreviewItems()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, previewResp{OK: false, Message: "读取模板补充预览失败"})
		return
	}
	writeJSON(w, http.StatusOK, previewResp{
		OK:      true,
		Items:   items,
		Message: fmt.Sprintf("共 %d 条", len(items)),
	})
}

func previewDetailHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "方法不允许", http.StatusMethodNotAllowed)
		return
	}
	items, err := listPreviewDetailItems()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, previewDetailResp{OK: false, Message: "读取指标明细失败"})
		return
	}
	writeJSON(w, http.StatusOK, previewDetailResp{
		OK:      true,
		Items:   items,
		Message: fmt.Sprintf("共 %d 条", len(items)),
	})
}

func statsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "方法不允许", http.StatusMethodNotAllowed)
		return
	}
	detailItems, err := listPreviewDetailItems()
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, statsResp{OK: false, Message: "读取统计数据失败"})
		return
	}

	l3ByDomainMap := map[string]*statsDomainRow{}
	l2ByDomainSet := map[string]map[string]bool{}
	l2ByDomainL2ExtSet := map[string]map[string]map[string]bool{}
	l3ByDomainL2Map := map[string]*statsL2Row{}

	domainOrder := []string{"安全物理环境", "安全通信网络", "安全区域边界", "安全计算环境", "安全管理中心", "安全管理制度", "安全管理机构", "安全管理人员", "安全建设管理", "安全运维管理", "云扩展"}
	orderIndex := map[string]int{}
	for i, d := range domainOrder {
		orderIndex[d] = i
	}

	for _, it := range detailItems {
		d := strings.TrimSpace(it.Domain)
		if d == "" {
			d = "安全计算环境"
		}
		l2 := strings.TrimSpace(it.Level2)
		if l2 == "" {
			continue
		}
		ext := strings.TrimSpace(it.ExtensionType)
		if ext == "" {
			ext = "general"
		}

		if _, ok := l3ByDomainMap[d]; !ok {
			l3ByDomainMap[d] = &statsDomainRow{Domain: d}
		}
		if _, ok := l2ByDomainSet[d]; !ok {
			l2ByDomainSet[d] = map[string]bool{}
		}
		if _, ok := l2ByDomainL2ExtSet[d]; !ok {
			l2ByDomainL2ExtSet[d] = map[string]map[string]bool{}
		}
		if _, ok := l2ByDomainL2ExtSet[d][l2]; !ok {
			l2ByDomainL2ExtSet[d][l2] = map[string]bool{}
		}
		l2ByDomainSet[d][l2] = true

		k := d + "\x00" + l2
		if _, ok := l3ByDomainL2Map[k]; !ok {
			l3ByDomainL2Map[k] = &statsL2Row{Domain: d, Level2: l2}
		}

		incDomain := func(row *statsDomainRow) {
			row.TotalCount++
			switch ext {
			case "cloud":
				row.CloudCount++
			case "mobile":
				row.MobileCount++
			case "iot":
				row.IotCount++
			case "industrial":
				row.IndustrialCount++
			default:
				row.GeneralCount++
			}
		}
		incL2 := func(row *statsL2Row) {
			row.TotalCount++
			switch ext {
			case "cloud":
				row.CloudCount++
			case "mobile":
				row.MobileCount++
			case "iot":
				row.IotCount++
			case "industrial":
				row.IndustrialCount++
			default:
				row.GeneralCount++
			}
		}
		incDomain(l3ByDomainMap[d])
		incL2(l3ByDomainL2Map[k])

		if !l2ByDomainL2ExtSet[d][l2][ext] {
			l2ByDomainL2ExtSet[d][l2][ext] = true
		}
	}

	l3ByDomain := make([]statsDomainRow, 0, len(l3ByDomainMap))
	for _, v := range l3ByDomainMap {
		l3ByDomain = append(l3ByDomain, *v)
	}

	l2ByDomain := make([]statsDomainRow, 0, len(l2ByDomainSet))
	for d, l2set := range l2ByDomainSet {
		row := statsDomainRow{Domain: d}
		for l2 := range l2set {
			extSet := l2ByDomainL2ExtSet[d][l2]
			if extSet["general"] {
				row.GeneralCount++
			}
			if extSet["cloud"] {
				row.CloudCount++
			}
			if extSet["mobile"] {
				row.MobileCount++
			}
			if extSet["iot"] {
				row.IotCount++
			}
			if extSet["industrial"] {
				row.IndustrialCount++
			}
			if len(extSet) > 0 {
				row.TotalCount++
			}
		}
		l2ByDomain = append(l2ByDomain, row)
	}

	l3ByDomainL2 := make([]statsL2Row, 0, len(l3ByDomainL2Map))
	for _, v := range l3ByDomainL2Map {
		l3ByDomainL2 = append(l3ByDomainL2, *v)
	}

	sort.Slice(l2ByDomain, func(i, j int) bool {
		ai, aok := orderIndex[l2ByDomain[i].Domain]
		aj, bok := orderIndex[l2ByDomain[j].Domain]
		if aok && bok && ai != aj {
			return ai < aj
		}
		if aok != bok {
			return aok
		}
		return l2ByDomain[i].Domain < l2ByDomain[j].Domain
	})
	sort.Slice(l3ByDomain, func(i, j int) bool {
		ai, aok := orderIndex[l3ByDomain[i].Domain]
		aj, bok := orderIndex[l3ByDomain[j].Domain]
		if aok && bok && ai != aj {
			return ai < aj
		}
		if aok != bok {
			return aok
		}
		return l3ByDomain[i].Domain < l3ByDomain[j].Domain
	})
	sort.Slice(l3ByDomainL2, func(i, j int) bool {
		ai, aok := orderIndex[l3ByDomainL2[i].Domain]
		aj, bok := orderIndex[l3ByDomainL2[j].Domain]
		if aok && bok && ai != aj {
			return ai < aj
		}
		if aok != bok {
			return aok
		}
		if l3ByDomainL2[i].Domain != l3ByDomainL2[j].Domain {
			return l3ByDomainL2[i].Domain < l3ByDomainL2[j].Domain
		}
		return l3ByDomainL2[i].Level2 < l3ByDomainL2[j].Level2
	})

	writeJSON(w, http.StatusOK, statsResp{
		OK:           true,
		L2ByDomain:   l2ByDomain,
		L3ByDomain:   l3ByDomain,
		L3ByDomainL2: l3ByDomainL2,
		Message:      "统计成功",
	})
}

func listPreviewItems() ([]previewItem, error) {
	b, err := os.ReadFile(previewPath)
	if err != nil {
		return nil, err
	}
	items := make([]previewItem, 0, 128)
	if err := json.Unmarshal(b, &items); err != nil {
		return nil, err
	}
	return items, nil
}

func listPreviewDetailItems() ([]previewDetailItem, error) {
	b, err := os.ReadFile(detailPath)
	if err != nil {
		return nil, err
	}
	items := make([]previewDetailItem, 0, 1024)
	if err := json.Unmarshal(b, &items); err != nil {
		return nil, err
	}
	return items, nil
}

func listFiles() ([]fileItem, error) {
	items := make([]fileItem, 0, 64)
	for _, cat := range categories {
		catPath := filepath.Join(baseDir, cat)
		_ = os.MkdirAll(catPath, 0o755)
		err := filepath.WalkDir(catPath, func(path string, d fs.DirEntry, err error) error {
			if err != nil {
				return nil
			}
			if d.IsDir() {
				return nil
			}
			info, statErr := d.Info()
			if statErr != nil {
				return nil
			}
			rel, relErr := filepath.Rel(baseDir, path)
			if relErr != nil {
				return nil
			}
			rel = filepath.ToSlash(rel)
			parts := strings.Split(rel, "/")
			batch := ""
			if len(parts) >= 2 {
				batch = parts[1]
			}
			items = append(items, fileItem{
				Name:     info.Name(),
				RelPath:  rel,
				Category: cat,
				Batch:    batch,
				Size:     info.Size(),
				ModTime:  info.ModTime().Format("2006-01-02 15:04:05"),
			})
			return nil
		})
		if err != nil {
			return nil, err
		}
	}

	sort.Slice(items, func(i, j int) bool {
		if items[i].Category != items[j].Category {
			return items[i].Category < items[j].Category
		}
		if items[i].Batch != items[j].Batch {
			return items[i].Batch > items[j].Batch
		}
		return items[i].Name < items[j].Name
	})
	return items, nil
}

func deleteFile(relPath string) error {
	relPath = filepath.ToSlash(strings.TrimSpace(relPath))
	if relPath == "" {
		return errors.New("缺少文件路径")
	}
	if strings.HasPrefix(relPath, "/") || strings.Contains(relPath, "../") || strings.Contains(relPath, "..\\") {
		return errors.New("非法路径")
	}

	abs := filepath.Clean(filepath.Join(baseDir, filepath.FromSlash(relPath)))
	baseClean := filepath.Clean(baseDir) + string(os.PathSeparator)
	if !strings.HasPrefix(abs+string(os.PathSeparator), baseClean) {
		return errors.New("非法路径")
	}

	if _, err := os.Stat(abs); err != nil {
		if os.IsNotExist(err) {
			return errors.New("文件不存在")
		}
		return errors.New("无法访问目标文件")
	}
	if err := os.Remove(abs); err != nil {
		return errors.New("删除失败")
	}
	cleanupEmptyParents(filepath.Dir(abs))
	return nil
}

func cleanupEmptyParents(start string) {
	base := filepath.Clean(baseDir)
	cur := filepath.Clean(start)
	for strings.HasPrefix(cur, base) && cur != base {
		err := os.Remove(cur)
		if err != nil {
			return
		}
		cur = filepath.Dir(cur)
	}
}

func saveOneFile(dstDir string, fh *multipart.FileHeader) (string, error) {
	in, err := fh.Open()
	if err != nil {
		return "", err
	}
	defer in.Close()

	name := sanitizeName(fh.Filename)
	if name == "" {
		name = fmt.Sprintf("file_%d", time.Now().UnixNano())
	}

	dst := filepath.Join(dstDir, name)
	if _, err := os.Stat(dst); err == nil {
		ext := filepath.Ext(name)
		base := strings.TrimSuffix(name, ext)
		dst = filepath.Join(dstDir, fmt.Sprintf("%s_%d%s", base, time.Now().UnixNano(), ext))
	}

	out, err := os.Create(dst)
	if err != nil {
		return "", err
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return "", err
	}
	return filepath.Base(dst), nil
}

func sanitizeName(s string) string {
	s = strings.TrimSpace(s)
	s = strings.ReplaceAll(s, "\\", "_")
	s = strings.ReplaceAll(s, "/", "_")
	s = safeName.ReplaceAllString(s, "_")
	return strings.TrimSpace(s)
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
