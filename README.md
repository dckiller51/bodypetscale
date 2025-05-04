<p align="center">
  <img src="https://raw.githubusercontent.com/dckiller51/bodypetscale/main/logo/Logo%20BodyPetScale.png" alt="BodyPetScale Logo" width="150">
</p>

# BodyPetScale

[![GH-release](https://img.shields.io/github/v/release/dckiller51/bodypetscale.svg?style=flat-square)](https://github.com/dckiller51/bodypetscale/releases)
[![GH-downloads](https://img.shields.io/github/downloads/dckiller51/bodypetscale/total?style=flat-square)](https://github.com/dckiller51/bodypetscale/releases)
[![GH-last-commit](https://img.shields.io/github/last-commit/dckiller51/bodypetscale.svg?style=flat-square)](https://github.com/dckiller51/bodypetscale/commits/main)
[![GH-code-size](https://img.shields.io/github/languages/code-size/dckiller51/bodypetscale.svg?color=red&style=flat-square)](https://github.com/dckiller51/bodypetscale)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=flat-square)](https://github.com/hacs)

## Track Your Loyal Companion's Health with BodyPetScale

With this Home Assistant integration, closely monitor the weight and potentially other health indicators of your dog or cat using data from their weight sensor. Gain valuable insights to help them maintain their ideal weight and vitality.

## How it Works

BodyPetScale uses your pet's weighing data, collected by their sensor and integrated into Home Assistant. Although this initial version primarily focuses on weight tracking, it provides a foundation for future enhancements that may include weight-based estimations (keep in mind that these estimations do not replace veterinary advice). All calculations are performed locally within your Home Assistant instance, ensuring the privacy of your data.

**Key Points for Dogs and Cats:**

* **Weight Tracking:** Visualize your pet's weight changes over time to quickly detect any significant weight gain or loss, which could be a sign of a health issue.
* **Ideal Weight (Estimation):** Based on the current weight, this integration may provide you with an estimation of your pet's ideal weight. **However, it is crucial to consult your veterinarian to determine your pet's specific ideal weight.**

Here's a breakdown of the process:

1. **Data Input:** Bodypetscale relies on data provided by your configured weight sensor. This can be:
   - A `sensor` entity that's already integrated with Home Assistant.
   - An `input_number` entity that's already integrated with Home Assistant.

2. **Calculations:** The integration uses formulas to estimate your pet's ideal weight, based on the weight provided and the configured pet type. **Please note that these estimates are not a substitute for veterinary advice.**

3. **Output:** The calculated metrics are then made available as new `sensor` entities within Home Assistant. You can then use these sensors in your Lovelace dashboards, automations, or any other Home Assistant feature.

**Key Considerations:**

* **No External Services:** Bodypetscale performs all calculations locally within your Home Assistant instance. No data is sent to external services or the internet.

**Example:**

Let's say you've configured a weight sensor called `sensor.my_weight`. When you add the Bodypetscale integration, it will:

1. Read the current value of `sensor.my_weight`.
2. Use this value (along with other information such as the animal type provided during setup) to calculate your ideal weight.
3. Create new sensors, such as `sensor.myname_weight_ideal` and `sensor.myname_body_type`, containing these calculated values.

## Prerequisites

Before installing Bodypetscale, make sure you have the following:

1. **A dedicated pet weight sensor in Home Assistant**: There is no connection between Bodypetscale and a specific smart scale. Bodypetscale works with any weight sensor integrated into Home Assistant. This can be:
   - A `sensor` entity dedicated to your pet. **Warning:** Using a sensor directly from a scale can cause complications.
   - An `input_number` entity provides a robust solution for recording your weight measurements in Home Assistant, with the crucial advantage of data persistence even after a system restart.
   **Important:** Each pet in Bodypetscale must have its own dedicated weight sensor. This sensor must be persistent, meaning that the data remains available when Home Assistant is restarted. Indeed, Bodypetscale retrieves the sensor value when it is initialized, which will distort the calculation data if the sensor is unavailable or at zero.

2. **Home Assistant installed.**

**(Optional) Last weigh-in sensor dedicated to the pet:**

If you plan to integrate your own last weigh-in sensor, make sure a dedicated sensor is properly configured in Home Assistant. The same recommendation applies: each pet should have their own last weigh-in sensor for optimal results.

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
2. Search for "Bodypetscale".
3. **Personalize your integration:**
   - **First Name (or other identifier):** Enter your first name or another identifier. **Important:** This identifier will determine the name of your Bodypetscale component in Home Assistant, as well as the names of all sensors created by it. Choose a clear and relevant name.
   - **Animal type (Cat/Dog):** Select your animal type. This choice may influence the estimation formulas used.
4. **Select your body type** A link is available to help you choose.
5. **Select your weight sensor:** Choose the existing weight sensor in Home Assistant (e.g., a `sensor`, or an `input_number`).
   - **Important Recommendation:** It is **strongly recommended** that each Bodypetscale user has their own dedicated weight sensor. Using a shared weight sensor (e.g., one directly linked to a scale) can cause issues when Home Assistant restarts. This is because Bodypetscale retrieves the sensor's value upon initialization, which can skew calculations if multiple users weigh themselves successively on the same scale before the restart.
6. **Last measurement time sensor (optional):**
   If you have a last weigh-in sensor, select it here (e.g., a `sensor`, or an `input_datetime`). This sensor is used to record the date and time of the most recent measurement.
   Recommendation: Just like the weight and impedance sensors, it is strongly recommended that each user has their own dedicated last weigh-in sensor to prevent conflicts or errors during Home Assistant restarts.
7. Click "Save".

**Explanation of choices:**

* **First Name/Identifier:** This field is important because it allows you to personalize the integration and avoid conflicts if multiple pet use Bodypetscale in your home. The name you choose will be used to name the entities created by the integration (e.g., `sensor.firstname_ideal_weight`, `sensor.firstname_body_type`, etc.).

## FAQ

## Helps create weight and/or last weighing data persistently

For a detailed configuration to integrate data persistence and multi-user management, please refer to the [example_config](example_config/) folder.

This folder contains example configurations for generating weight, impedance, and last weighing sensors, using both ESPHome and Home Assistant.

### Configuration Examples in the example_config Folder

The [example_config](example_config/) folder contains the following example configuration files:

* **`esphome_configuration.yaml`**: Complete ESPHome configuration to generate sensors directly from the Xiaomi Mi Scale.
* **`weight_impedance_update.yaml`**: Home Assistant configuration to generate sensors via the ESPHome integration or BLE Monitor.
* **`interactive_notification_user_selection_weight_data_update.yaml`**: Example automation created from the blueprint for user selection and weight data update via interactive notification.

Please consult the configuration files within the [example_config](example_config/) folder for detailed information on generating weight, impedance, and last weighing sensors.

## Useful links

* [ESPHome for Xiaomi Mi Scale](https://esphome.io/components/sensor/xiaomi_miscale.html)
* [BLE Monitor for Xiaomi Mi Scale](https://github.com/custom-components/ble_monitor)
