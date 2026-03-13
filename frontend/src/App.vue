<template>
  <a-layout style="min-height: 100vh">
    <a-layout-header style="color: white; font-size: 18px">
      IPC 性能数据查询 / 导入
    </a-layout-header>
    <a-layout-content style="padding: 24px">
      <a-card title="查询条件" :loading="loadingOptions">
        <a-form layout="inline" :model="filters" style="row-gap: 12px">
          <a-form-item label="IPC型号">
            <a-select
              v-model:value="filters.ipc_model_ids"
              mode="multiple"
              style="width: 260px"
              :options="ipcModelOptions"
              placeholder="可多选"
              :allow-clear="true"
            />
          </a-form-item>

          <a-form-item label="版本">
            <a-select
              v-model:value="filters.software_versions"
              mode="multiple"
              style="width: 240px"
              :options="(options?.software_versions || []).map((v) => ({ label: v, value: v }))"
              placeholder="可多选"
              :allow-clear="true"
            />
          </a-form-item>

          <a-form-item label="分辨率(MP)">
            <a-select
              v-model:value="filters.resolution_mp"
              style="width: 140px"
              :options="options?.resolutions.map((r) => ({ label: r + ' MP', value: r }))"
              allow-clear
            />
          </a-form-item>

          <a-form-item label="相机数量">
            <a-select
              v-model:value="filters.camera_count"
              style="width: 140px"
              :options="options?.camera_counts.map((c) => ({ label: c, value: c }))"
              allow-clear
            />
          </a-form-item>

          <a-form-item label="模型数量">
            <a-select
              v-model:value="filters.model_count"
              style="width: 140px"
              :options="options?.model_counts.map((m) => ({ label: m, value: m }))"
              allow-clear
            />
          </a-form-item>

          <a-form-item>
            <a-space>
              <a-button type="primary" :loading="loadingTable" @click="doSearch">
                查询
              </a-button>
              <a-button @click="resetFilters">重置</a-button>
              <a-button :disabled="tableData.length === 0" @click="exportCsv">
                导出 CSV
              </a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </a-card>

      <a-card v-if="showImportSection" title="导入 CSV" style="margin-top: 16px">
        <a-space>
          <a-button type="primary" @click="showImportModal = true">导入 CSV</a-button>
          <a-button @click="downloadTemplate">下载导入模板</a-button>
        </a-space>
        <div style="margin-top: 8px; color: #888">
          点击按钮后在弹窗中选择文件并手动触发上传；模板示例可下载查看。
        </div>
      </a-card>

      <a-card title="查询结果" style="margin-top: 16px">
        <a-table
          :data-source="tableData"
          :columns="columns"
          :loading="loadingTable"
          row-key="id"
          size="small"
          :pagination="pagination"
          @change="handleTableChange"
        />
      </a-card>

      <a-modal
        v-model:open="showImportModal"
        title="导入 CSV"
        :confirm-loading="importing"
        :footer="null"
        destroy-on-close
      >
        <a-upload
          v-model:file-list="fileList"
          :before-upload="handleBeforeUpload"
          :max-count="1"
          accept=".csv"
          @remove="handleRemove"
        >
          <a-button>
            <template #icon><upload-outlined /></template>
            选择文件
          </a-button>
        </a-upload>
        <div style="margin-top: 8px; color: #888">
          列顺序：IPC型号, 分辨率(MP), 相机数量, 照片数量, 是否存图, 版本, 性能(MP/s), 极限性能(MP/s)
        </div>
        <a-space style="margin-top: 16px">
          <a-button
            type="primary"
            :disabled="!fileList.length"
            :loading="importing"
            @click="submitImport"
          >
            上传并导入
          </a-button>
          <a-button @click="closeImportModal">取消</a-button>
        </a-space>
      </a-modal>
    </a-layout-content>
  </a-layout>
</template>

<script setup lang="ts">
import { UploadOutlined } from "@ant-design/icons-vue";
import {
  message,
  TableColumnsType,
  TablePaginationConfig,
  UploadProps,
  UploadChangeParam,
  UploadFile
} from "ant-design-vue";
import { ref, onMounted, computed, onBeforeUnmount } from "vue";
import {
  fetchOptions,
  searchRecords,
  importRecords
} from "./api";
import type { OptionsResponse, TestRecord, RecordSearchRequest } from "./types";

const options = ref<OptionsResponse>();
const loadingOptions = ref(false);
const loadingTable = ref(false);
const importing = ref(false);
const tableData = ref<TestRecord[]>([]);
const showImportModal = ref(false);
const fileList = ref<UploadFile[]>([]);
const showImportSection = ref(false);
const pagination = ref<TablePaginationConfig>({
  current: 1,
  pageSize: 20,
  showSizeChanger: true,
  pageSizeOptions: ["10", "20", "50", "100"],
  showTotal: (total) => `共 ${total} 条`
});

function handleTableChange(pag: TablePaginationConfig) {
  pagination.value = {
    ...pagination.value,
    current: pag.current,
    pageSize: pag.pageSize
  };
}

const filters = ref<RecordSearchRequest>({
  ipc_model_ids: [],
  resolution_mp: 12,
  camera_count: undefined,
  model_count: 2,
  software_versions: []
});

const ipcModelOptions = computed(() =>
  (options.value?.ipc_models || []).map((m) => ({
    label: m.name,
    value: m.id
  }))
);

const columns = ref<TableColumnsType>([
  { title: "IPC型号", dataIndex: ["ipc_model", "name"], key: "ipc_model" },
  { title: "版本", dataIndex: "software_version", key: "software_version" },
  { title: "分辨率(MP)", dataIndex: "resolution_mp", key: "resolution_mp" },
  { title: "相机数", dataIndex: "camera_count", key: "camera_count" },
  { title: "模型数", dataIndex: "model_count", key: "model_count" },
  { title: "照片数", dataIndex: "image_count", key: "image_count" },
  {
    title: "存图",
    dataIndex: "save_image",
    key: "save_image",
    customRender: ({ text }) => (text === true ? "是" : text === false ? "否" : "")
  },
  { title: "性能(MP/s)", dataIndex: "measured_perf_mps", key: "measured_perf_mps" },
  { title: "极限性能(MP/s)", dataIndex: "ex_perf_mps", key: "ex_perf_mps" },
  { title: "缺陷数", dataIndex: "segments_count", key: "segments_count" },
  {
    title: "创建时间",
    dataIndex: "created_at",
    key: "created_at",
    customRender: ({ text }) => (text ? new Date(text).toLocaleString() : "")
  }
]);

async function loadOptions() {
  loadingOptions.value = true;
  try {
    options.value = await fetchOptions();
  } catch (err: any) {
    message.error(err?.message || "加载选项失败");
  } finally {
    loadingOptions.value = false;
  }
}

async function doSearch() {
  loadingTable.value = true;
  try {
    tableData.value = await searchRecords(filters.value);
  } catch (err: any) {
    message.error(err?.message || "查询失败");
  } finally {
    loadingTable.value = false;
  }
}

function resetFilters() {
  filters.value = {
    ipc_model_ids: [],
    resolution_mp: 12,
    camera_count: undefined,
    model_count: 2,
    software_versions: []
  };
}

function exportCsv() {
  if (!tableData.value.length) return;
  const headers = [
    "IPC型号",
    "版本",
    "分辨率(MP)",
    "相机数",
    "模型数",
    "照片数",
    "存图",
    "性能(MP/s)",
    "极限性能(MP/s)",
    "缺陷数",
    "创建时间"
  ];
  const rows = tableData.value.map((r) => [
    r.ipc_model?.name ?? "",
    r.software_version ?? "",
    r.resolution_mp ?? "",
    r.camera_count ?? "",
    r.model_count ?? "",
    r.image_count ?? "",
    r.save_image === true ? "是" : r.save_image === false ? "否" : "",
    r.measured_perf_mps ?? "",
    r.ex_perf_mps ?? "",
    r.segments_count ?? "",
    r.created_at ? new Date(r.created_at).toISOString() : ""
  ]);
  const csv = [headers, ...rows]
    .map((row) =>
      row
        .map((v) => {
          const s = String(v ?? "");
          return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
        })
        .join(",")
    )
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "records.csv";
  a.click();
  URL.revokeObjectURL(url);
}

const handleBeforeUpload: UploadProps["beforeUpload"] = (file) => {
  fileList.value = [file];
  return false; // 阻止自动上传
};

function handleRemove() {
  fileList.value = [];
}

function closeImportModal() {
  showImportModal.value = false;
  fileList.value = [];
}

async function submitImport() {
  if (!fileList.value.length || !fileList.value[0].originFileObj) {
    message.warning("请先选择文件");
    return;
  }
  importing.value = true;
  try {
    const raw = fileList.value[0].originFileObj as File;
    const res = await importRecords(raw);
    message.success(
      `导入完成: 插入 ${res.inserted}, 跳过 ${res.skipped}` +
        (res.errors?.length ? `，错误 ${res.errors.length}` : "")
    );
    if (res.errors?.length) {
      console.warn("Import errors:", res.errors);
    }
    closeImportModal();
    await doSearch();
  } catch (err: any) {
    message.error(err?.message || "导入失败");
  } finally {
    importing.value = false;
  }
}

function downloadTemplate() {
  const link = document.createElement("a");
  link.href = "/Performance_Import_Template.csv";
  link.download = "Performance_Import_Template.csv";
  link.click();
}

function handleImportHotkey(event: KeyboardEvent) {
  if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "y") {
    showImportSection.value = !showImportSection.value;
    localStorage.setItem(
      "ipc_percalc_show_import",
      showImportSection.value ? "1" : "0"
    );
  }
}

onMounted(async () => {
  const envEnabled = import.meta.env.VITE_ENABLE_IMPORT === "true";
  const cached = localStorage.getItem("ipc_percalc_show_import");
  showImportSection.value = envEnabled || cached === "1";
  window.addEventListener("keydown", handleImportHotkey);
  await loadOptions();
  await doSearch();
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleImportHotkey);
});
</script>

<style scoped>
.ant-upload-hint {
  color: #888;
}
</style>
