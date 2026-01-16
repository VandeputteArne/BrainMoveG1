<script setup>
import ButtonsNext from '../../components/buttons/ButtonsNext.vue';
import OnboardingProgressBlock from '../../components/onboarding/OnboardingProgressBlock.vue';
</script>

<template>
  <div class="c-onboarding">
    <div class="c-onboarding__inhoud">
      <img class="c-onboarding__image" src="/images/BrainMove-Logo.png" alt="BrainMove Logo" />
      <div class="c-onboarding__text">
        <h1>BrainMove</h1>
        <h3 class="c-onboarding__h2">Beweeg slimmer, denk scherper</h3>
      </div>
    </div>
    <div class="c-onboarding__progress">
      <div class="c-onboarding__progess-blocks">
        <OnboardingProgressBlock :active="true" />
        <OnboardingProgressBlock :active="false" />
        <OnboardingProgressBlock :active="false" />
      </div>
      <ButtonsNext :progress="25" to="/setup" />
    </div>

    <div class="c-onboarding__circle c-onboarding__circle--1"></div>
    <div class="c-onboarding__circle c-onboarding__circle--2"></div>
  </div>
</template>

<style scoped>
.c-onboarding {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  padding: 0rem 1.25rem;

  position: relative;
  overflow: hidden;

  .c-onboarding__image {
    width: 60%;
    max-width: 20rem;
    height: auto;
  }

  .c-onboarding__text {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .c-onboarding__inhoud {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100%;
    gap: 2rem;
    margin-bottom: 4rem;
  }

  .c-onboarding__progress {
    position: absolute;
    bottom: 2rem;
  }

  .c-onboarding__circle {
    border-radius: 100%;
    z-index: -1;
  }

  .c-onboarding__circle--1 {
    position: absolute;
    width: 11rem;
    height: 11rem;
    top: -5rem;
    left: -5rem;

    background-color: var(--blue-40);
  }

  .c-onboarding__circle--2 {
    position: absolute;
    width: 11rem;
    height: 11rem;
    bottom: -5rem;
    right: -5rem;

    background-color: var(--blue-10);
  }

  .c-onboarding__progress {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
  }

  .c-onboarding__progess-blocks {
    display: flex;
    gap: 0.5rem;
  }

  .c-onboarding__h2 {
    text-align: center;
  }
}
</style>
