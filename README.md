<p align="center">
  <img src="https://raw.githubusercontent.com/dckiller51/bodypetscale/main/logo/Logo%20BodyPetScale.png" alt="BodyPetScale Logo" width="150">
</p>

# BodyPetScale

[![GH-release](https://img.shields.io/github/v/release/dckiller51/bodypetscale.svg?style=flat-square)](https://github.com/dckiller51/bodypetscale/releases)
[![GH-downloads](https://img.shields.io/github/downloads/dckiller51/bodypetscale/total?style=flat-square)](https://github.com/dckiller51/bodypetscale/releases)
[![GH-last-commit](https://img.shields.io/github/last-commit/dckiller51/bodypetscale.svg?style=flat-square)](https://github.com/dckiller51/bodypetscale/commits/main)
[![GH-code-size](https://img.shields.io/github/languages/code-size/dckiller51/bodypetscale.svg?color=red&style=flat-square)](https://github.com/dckiller51/bodypetscale)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=flat-square)](https://github.com/hacs)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Buy_me_a_coffee-F16061?style=flat-square&logo=ko-fi&logoColor=white)](https://ko-fi.com/dckiller)

## Track Your Loyal Companion's Health with BodyPetScale

With this Home Assistant integration, closely monitor the weight and potentially other health indicators of your dog or cat using data from their weight sensor. Gain valuable insights to help them maintain their ideal weight and vitality.

## How it Works

BodyPetScale uses your pet's weighing data, collected by their sensor and integrated into Home Assistant. Although this initial version primarily focuses on weight tracking, it provides a foundation for future enhancements that may include weight-based estimations (keep in mind that these estimations do not replace veterinary advice). All calculations are performed locally within your Home Assistant instance, ensuring the privacy of your data.

**Key Points for Dogs and Cats:**

- **Weight Tracking:** Visualize your pet's weight changes over time to quickly detect any significant weight gain or loss, which could be a sign of a health issue.
- **Ideal Weight (Estimation):** This integration estimates your pet's ideal weight based on the current weight and some predefined formulas. These estimates serve as a guideline only. **Please always consult a veterinarian for a more accurate determination of your pet's ideal weightt.**

Here's a breakdown of the process:

1. **Data Input:** Bodypetscale relies on data provided by your configured weight sensor. This can be:
      - A `sensor` entity that's already integrated with Home Assistant.
      - An `input_number` entity that's already integrated with Home Assistant.

2. **Calculations:** The integration uses formulas to estimate your pet's ideal weight, based on the weight provided and the configured pet type. **Please note that these estimates are not a substitute for veterinary advice.**

3. **Output:** The calculated metrics are then made available as new `sensor` entities within Home Assistant. You can then use these sensors in your Lovelace dashboards, automations, or any other Home Assistant feature.

**Key Considerations:**

- **No External Services:** Bodypetscale performs all calculations locally within your Home Assistant instance. No data is sent to external services or the internet.

**Example:**

Let's say you've configured a weight sensor called `sensor.my_weight`. When you add the Bodypetscale integration, it will:

1. Read the current value of `sensor.my_weight`.
2. Use this value (along with other information such as the animal type provided during setup) to calculate your ideal weight.
3. Create new sensors, such as `sensor.myname_weight_ideal` and `sensor.myname_body_type`, containing these calculated values.

## Prerequisites

Before installing Bodypetscale, make sure you have the following:

1. **A weight sensor in Home Assistant**: There is no connection between Bodypetscale and a specific smart scale. Bodypetscale works with any weight sensor integrated into Home Assistant. This can be:

   - The weight sensor of a scale **shared** by several pets and people. Bodypetscale identifies which pet is on the scale and keeps its last weight across restarts (see [Shared scale](#shared-scale-several-pets-on-one-scale)).
   - A `sensor` or `input_number` entity **dedicated** to your pet (identification method "None"). It must be persistent: Bodypetscale reads its value when it starts.

2. **Home Assistant installed.**

**(Optional) Last weigh-in sensor dedicated to the pet:**

If you plan to integrate your own last weigh-in sensor, make sure a dedicated sensor is properly configured in Home Assistant. With a shared scale this is not needed: the time of each accepted weighing is recorded automatically.

## Installation

### Via HACS

1. Open HACS in Home Assistant.
2. Go to the "Integrations" tab.
3. Search for "Bodypetscale".
4. Click "Install".

### Manual

1. Download the latest version archive from the [releases page](https://github.com/dckiller51/bodypetscale/releases).
2. Unzip the archive.
3. Copy the _entire_ `custom_components/bodypetscale` folder into your `config/custom_components` folder in Home Assistant. The final path should be `/config/custom_components/bodypetscale`.
4. Restart Home Assistant.

## Configuration

1. Open Home Assistant and go to "Settings" -> "Devices & Services" -> "Add Integration".
2. Search for "Bodypetscale" and click "Install".
3. **Configure your Pet’s Information:**

   - **First Name (or other identifier):** Enter your first name or another identifier. **Important:** This identifier will determine the names of all sensors created in Home Assistant. Choose a clear and relevant name.
   - **Animal Type (Cat/Dog):** Select your animal type. This choice may influence the estimation formulas used for energy calculations and other metrics.
   - **Birthday:** Enter your pet's birthday. This information is used to calculate the age and life stage of your animal.

4. **Configure Animal Characteristics:**

   - **Breed:** Select your pet’s breed. This will affect the energy calculation based on breed-specific factors.
   - **Activity:** Choose your pet's activity level (e.g., "Normal (1h walk)", "No outdoor access").
   - **Reproductive:** Indicate the reproductive status of your cat (e.g., "Neutered", "Spayed").
   - **Temperament (for Cats):** Choose your cat's temperament (e.g., "Calm", "Active").
   - **Appetite (for Dogs):** Indicate the appetite level of your dog (e.g., "Hearty eater", "Normal", "Small eater").

5. **Configure Sensors and Conditions:**

   - **Environment:** Select your pet's living environment (e.g., "Indoor", "Outdoors in winter"). This factor is used in energy needs estimation.
   - **Morphology:** Choose your pet’s body condition score, using the provided scale to estimate whether your animal is underweight, ideal, or overweight. You can refer to visual guides on [BodyPetScale's official website](https://dckiller51.github.io/bodypetscale/) to help determine this score.
   - **Weight Sensor:** Choose the weight sensor of the scale, or a sensor dedicated to this pet (e.g., a `sensor`, or an `input_number`).
   - **Last Measurement Time Sensor (optional):** If you have a last weigh-in sensor, select it here (e.g., a `sensor`, or an `input_datetime`). This sensor records the date and time of the most recent measurement.
   - **Stabilized Sensor (optional):** Binary sensor of the scale reporting a stable measurement. The weight is then read only once the measurement is stable.
   - **Holder Weight Sensor (optional):** Weight of the person who carries the pet on the scale. See [Weighing a pet in your arms](#weighing-a-pet-in-your-arms).
   - **Identification Method:** "None" for a dedicated sensor, or a method to share the scale (see below). Depending on the method, a last step asks for its settings.

6. **Save the Configuration:**

   - Click "Save" to finalize the configuration.

7. **Access New Sensors:**
   - Once the configuration is complete, the integration will create new sensors that you can use in your Lovelace dashboards, automations, and other Home Assistant features.

## Shared scale (several pets on one scale)

Like [bodymiscale](https://github.com/dckiller51/bodymiscale), Bodypetscale can use the single weight sensor of your scale for every pet. Each pet chooses how a measurement is attributed to it:

| Method             | How it works                                                                                               | Settings                                        |
| ------------------ | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **None**           | Dedicated sensor: every value is the weight of this pet (previous behaviour).                              | —                                               |
| **Weight range**   | The measurement is attributed if the weight is in `[min, max[`. The ranges of the pets must not overlap.   | Minimum and maximum weight                      |
| **Nearest weight** | The measurement is attributed to the pet whose last weight is the nearest, within the tolerance.           | Current weight of the pet, tolerance (2 kg)     |
| **Notification**   | Your phone receives an interactive notification after each weighing; tap the name of the pet on the scale. | Phone, optional minimum/maximum weight to offer |

The weight of the pet and the time of the measurement are stored by Bodypetscale, so they are kept after a restart even if someone else used the scale last. If the scale reports a stable measurement through a binary sensor, select it as **Stabilized Sensor** to ignore the intermediate values.

### Weighing a pet in your arms

Many pets will not stay alone on a scale. Set the **Holder Weight Sensor** to the weight of the person carrying the pet (for example their bodymiscale weight sensor, or an `input_number`). The holder weight is subtracted from the scale weight:

- **None:** the holder weight is always subtracted.
- **Weight range:** the pet is "alone" if the scale weight is in the range, otherwise "carried" if the net weight is in the range.
- **Nearest weight:** the nearest of the scale weight and the net weight is used.
- **Notification:** the notification offers two buttons, `Rex` (alone) and `Rex (carried)`.

The holder weight is read at the moment of the weighing, so the result stays correct if the person's own profile is updated with the carried weight just afterwards. The main sensor exposes a `weighing_mode` attribute: `alone` or `held`.

**Using bodymiscale on the same scale:** when you weigh yourself with your pet, your bodymiscale profile may also accept this weight as your own. Use a narrow weight range or tolerance for your own profile, or the notification method, so that the carried weight is not recorded as your weight.

**Notification buttons:** Android shows at most 3 buttons per notification. With several pets, use the optional minimum/maximum weights so that only the relevant pets are offered.

## FAQ

## Helps create weight and/or last weighing data persistently

For a detailed configuration to integrate data persistence and multi-user management, please refer to the [example_config](example_config/) folder.

This folder contains example configurations for generating weight, impedance, and last weighing sensors, using both ESPHome and Home Assistant.

### Configuration Examples in the example_config Folder

The [example_config](example_config/) folder contains the following example configuration files:

- **`esphome_configuration.yaml`**: Complete ESPHome configuration to generate sensors directly from the Xiaomi Mi Scale.
- **`weight_impedance_update.yaml`**: Home Assistant configuration to generate sensors via the ESPHome integration or BLE Monitor.
- **`interactive_notification_user_selection_weight_data_update.yaml`**: Example automation created from the blueprint for user selection and weight data update via interactive notification.

Please consult the configuration files within the [example_config](example_config/) folder for detailed information on generating weight, impedance, and last weighing sensors.

## Useful links

- [ESPHome for Xiaomi Mi Scale](https://esphome.io/components/sensor/xiaomi_miscale.html)
- [BLE Monitor for Xiaomi Mi Scale](https://github.com/custom-components/ble_monitor)

## ☕ Support

If you find **BodyPetScale** useful and want to support its development, you can buy me a coffee!

[![Ko-fi](https://img.shields.io/badge/Buy_me_a_coffee-Ko--fi-F16061?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/dckiller)
