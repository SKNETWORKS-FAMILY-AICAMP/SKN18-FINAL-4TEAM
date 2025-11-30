<template>
  <div class="code-editor-wrapper">
    <textarea ref="textarea"></textarea>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import CodeMirror from "codemirror";
import "codemirror/lib/codemirror.css";
import "codemirror/mode/python/python.js";
import "codemirror/mode/clike/clike.js";

const props = defineProps({
  modelValue: {
    type: String,
    default: ""
  },
  mode: {
    type: String,
    default: "text/x-csrc"
  }
});

const emit = defineEmits(["update:modelValue"]);

const textarea = ref(null);
let editor = null;

onMounted(() => {
  editor = CodeMirror.fromTextArea(textarea.value, {
    value: props.modelValue,
    mode: props.mode,
    lineNumbers: true,
    lineWrapping: false,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    theme: "default"
  });

  editor.setValue(props.modelValue || "");

  editor.on("change", () => {
    const val = editor.getValue();
    if (val !== props.modelValue) {
      emit("update:modelValue", val);
    }
  });
});

watch(
  () => props.modelValue,
  (val) => {
    if (editor && val !== editor.getValue()) {
      editor.setValue(val || "");
    }
  }
);

watch(
  () => props.mode,
  (val) => {
    if (editor) {
      editor.setOption("mode", val);
    }
  }
);

onBeforeUnmount(() => {
  if (editor) {
    editor.toTextArea();
    editor = null;
  }
});
</script>

<style scoped>
.code-editor-wrapper {
  height: 100%;
}

.code-editor-wrapper :deep(.CodeMirror) {
  height: 100%;
  border-radius: 12px;
  border: 1px solid #1f2937;
  background: #020617;
  color: #e5e7eb;
  font-size: 13px;
}

.code-editor-wrapper :deep(.CodeMirror-cursor) {
  border-left: 2px solid #f97316;
}

.code-editor-wrapper :deep(.CodeMirror-selected) {
  background: rgba(56, 189, 248, 0.2);
}

.code-editor-wrapper :deep(.cm-keyword) {
  color: #38bdf8;
}

.code-editor-wrapper :deep(.cm-string) {
  color: #fbbf24;
}

.code-editor-wrapper :deep(.cm-comment) {
  color: #6b7280;
  font-style: italic;
}

.code-editor-wrapper :deep(.cm-number) {
  color: #a855f7;
}

.code-editor-wrapper :deep(.cm-variable) {
  color: #e5e7eb;
}

.code-editor-wrapper :deep(.cm-variable-2) {
  color: #4ade80;
}

.code-editor-wrapper :deep(.cm-builtin),
.code-editor-wrapper :deep(.cm-def) {
  color: #f97316;
}

.code-editor-wrapper :deep(.cm-operator) {
  color: #e5e7eb;
}
</style>
