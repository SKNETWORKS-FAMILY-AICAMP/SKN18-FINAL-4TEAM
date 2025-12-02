<template>
  <Transition name="route-fade" mode="out-in">
    <RouterView />
  </Transition>
</template>

<script setup>
import { RouterView } from "vue-router";
</script>

<style>
html,
body,
#app {
  margin: 0;
  padding: 0;
}

.route-fade-enter-active,
.route-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.route-fade-enter-from,
.route-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
