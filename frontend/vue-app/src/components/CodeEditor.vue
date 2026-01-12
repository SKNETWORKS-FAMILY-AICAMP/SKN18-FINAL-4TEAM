<template>
  <div class="code-editor-wrapper">
    <textarea ref="textarea"></textarea>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import CodeMirror from "codemirror";
import "codemirror/lib/codemirror.css";
import "codemirror/addon/selection/active-line.js";
import "codemirror/addon/edit/matchbrackets.js";
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
  },
  readOnly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(["update:modelValue", "editor-keydown", "editor-copy"]);

const textarea = ref(null);
let editor = null;
let copyListenerCleanup = null;
let indentGuideOverlay = null;

const buildIndentGuideOverlay = (indentUnit) => ({
  token(stream) {
    const line = stream.string || "";
    const pos = stream.pos;
    const before = line.slice(0, pos);
    if (!/^[\t ]*$/.test(before)) {
      stream.skipToEnd();
      return null;
    }
    const ch = stream.peek();
    if (ch === "\t") {
      stream.next();
      return "indent-guide";
    }
    if (ch === " ") {
      const rest = line.slice(pos);
      const match = rest.match(/^[ ]+/);
      if (match) {
        const take = Math.min(indentUnit, match[0].length);
        stream.pos += take;
        return "indent-guide";
      }
    }
    stream.skipToEnd();
    return null;
  }
});

onMounted(() => {
  editor = CodeMirror.fromTextArea(textarea.value, {
    value: props.modelValue,
    mode: props.mode,
    lineNumbers: true,
    lineWrapping: false,
    indentUnit: 4,
    tabSize: 4,
    indentWithTabs: false,
    styleActiveLine: true,
    matchBrackets: true,
    theme: "default",
    readOnly: props.readOnly ? "nocursor" : false
  });

  editor.setValue(props.modelValue || "");
  indentGuideOverlay = buildIndentGuideOverlay(
    editor.getOption("indentUnit") || 4
  );
  editor.addOverlay(indentGuideOverlay);

  editor.on("change", () => {
    const val = editor.getValue();
    if (val !== props.modelValue) {
      emit("update:modelValue", val);
    }
  });

  editor.on("keydown", (_cm, event) => {
    emit("editor-keydown", event);
  });

  const wrapperEl = editor.getWrapperElement();
  const handleCopy = (event) => emit("editor-copy", event);

  if (wrapperEl && wrapperEl.addEventListener) {
    wrapperEl.addEventListener("copy", handleCopy);
    copyListenerCleanup = () => wrapperEl.removeEventListener("copy", handleCopy);
  }
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

watch(
  () => props.readOnly,
  (val) => {
    if (editor) {
      editor.setOption("readOnly", val ? "nocursor" : false);
    }
  }
);

onBeforeUnmount(() => {
  if (editor) {
    if (indentGuideOverlay) {
      editor.removeOverlay(indentGuideOverlay);
      indentGuideOverlay = null;
    }
    editor.toTextArea();
    editor = null;
  }
  if (copyListenerCleanup) {
    copyListenerCleanup();
    copyListenerCleanup = null;
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

.code-editor-wrapper :deep(.CodeMirror-activeline-background) {
  background: rgba(56, 189, 248, 0.12);
}

.code-editor-wrapper :deep(.CodeMirror-activeline-gutter) {
  background: rgba(56, 189, 248, 0.2);
}

.code-editor-wrapper :deep(.cm-indent-guide) {
  background-image: linear-gradient(
    to right,
    rgba(148, 163, 184, 0.35) 1px,
    transparent 1px
  );
  background-position: right;
  background-repeat: no-repeat;
  background-size: 1px 100%;
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
