const sliderContainer = document.querySelector('.slider-container');
const slider = document.getElementById('slider');
const scoreLabels = document.querySelectorAll('.score-labels span');
const bcsImage = document.getElementById('bcsImage');
const scoreDescription = document.getElementById('scoreDescription');
const animalTypeSelect = document.getElementById('animalType');
const animalInfoContainer = document.getElementById('animalInfo');

const scoreDescriptions = {
    cat: {
        '1': {
            title: "1 Very thin",
            description: [
                "Ribs, spine and pelvic bones easily visible on shorthaired cats",
                "Very narrow waist",
                "Small amount of muscle",
                "No palpable fat on the rib cage",
                "Severe abdominal tuck"
            ]
        },
        '2': {
            title: "2 Underweight",
            description: [
                "Ribs easily visible on shorthaired cats",
                "Very narrow waist",
                "Loss of muscle mass",
                "No palpable fat on the rib cage",
                "Very pronounced abdominal tuck"
            ]
        },
        '3': {
            title: "3 Slightly underweight",
            description: [
                "Ribs visible on shorthaired cats",
                "Obvious waist",
                "Very small amount of abdominal fat",
                "Marked abdominal tuck"
            ]
        },
        '4': {
            title: "4 Ideal",
            description: [
                "Ribs not visible but are easily palpable",
                "Obvious waist",
                "Minimal amount of abdominal fat"
            ]
        },
        '5': {
            title: "5 Ideal",
            description: [
                "Well proportioned",
                "Ribs not visible but are easily palpable",
                "Obvious waist",
                "Small amount of abdominal fat",
                "Slight abdominal tuck"
            ]
        },
        '6': {
            title: "6 Slightly overweight",
            description: [
                "Ribs not visible but palpable",
                "Waist not clearly defined when seen from above",
                "Very slight abdominal tuck"
            ]
        },
        '7': {
            title: "7 Overweight",
            description: [
                "Ribs difficult to palpate under the fat",
                "Waist barely visible",
                "No abdominal tuck",
                "Rounding of abdomen with moderate abdominal pad"
            ]
        },
        '8': {
            title: "8 Obese",
            description: [
                "Ribs not palpable under the fat",
                "Waist not visible",
                "Slight abdominal distension"
            ]
        },
        '9': {
            title: "9 Very obese",
            description: [
                "Ribs not palpable under a thick layer of fat",
                "Waist absent",
                "Obvious abdominal distension",
                "Extensive abdominal fat deposits"
            ]
        }
    },
    dog: {
        '1': {
            title: "1 Very thin",
            description: [
                "Ribs, lumbar vertebrae, pelvic bones and all bony prominences evident from a distance",
                "No discernible body fat",
                "Obvious loss of muscle mass"
            ]
        },
        '2': {
            title: "2 Underweight",
            description: [
                "Ribs, lumbar vertebrae, and pelvic bones easily visible",
                "No palpable fat",
                "Some bony prominences visible from a distance",
                "Minimal loss of muscle mass"
            ]
        },
        '3': {
            title: "3 Slightly underweight",
            description: [
                "Ribs easily palpable and may be visible with no palpable fat",
                "Tops of lumber vertebrae visible, pelvic bones becoming prominent",
                "Obvious waist and abdominal tuck"
            ]
        },
        '4': {
            title: "4 Ideal",
            description: [
                "Ribs easily palpable with minimal fat covering",
                "Waist easily noted when viewed from above",
                "Abdominal tuck evident"
            ]
        },
        '5': {
            title: "5 Ideal",
            description: [
                "Ribs palpable without excess fat covering",
                "Waist observed behind ribs when viewed from above",
                "Abdomen tucked up when viewed from side"
            ]
        },
        '6': {
            title: "6 Slightly overweight",
            description: [
                "Ribs palpable with slight excess of fat covering",
                "Waist is discernible when viewed from above but is not prominent",
                "Abdominal tuck apparent"
            ]
        },
        '7': {
            title: "7 Overweight",
            description: [
                "Ribs palpable with difficulty, heavy fat cover",
                "Noticeable fat deposits over lumbar area and base of tail",
                "Waist absent or barely visible",
                "Abdominal tuck may be absent"
            ]
        },
        '8': {
            title: "8 Obese",
            description: [
                "Ribs not palpable under very heavy fat cover or palpable only with significant pressure",
                "Heavy fat deposits over lumbar area and base of tail",
                "Waist absent",
                "No abdominal tuck",
                "Obvious abdominal distension may be present"
            ]
        },
        '9': {
            title: "9 Very obese",
            description: [
                "Massive fat deposits over thorax, spine, and base of tail",
                "Waist and abdominal tuck absent",
                "Fat deposits on neck and limbs",
                "Obvious abdominal distension"
            ]
        }
    }
};

const dogImages = {
    xsmall: [
        'pictures/dog/xsmall/1.png',
        'pictures/dog/xsmall/2.png',
        'pictures/dog/xsmall/3.png',
        'pictures/dog/xsmall/4.png',
        'pictures/dog/xsmall/5.png',
        'pictures/dog/xsmall/6.png',
        'pictures/dog/xsmall/7.png',
        'pictures/dog/xsmall/8.png',
        'pictures/dog/xsmall/9.png'
    ],
    small: [
        'pictures/dog/small/1.png',
        'pictures/dog/small/2.png',
        'pictures/dog/small/3.png',
        'pictures/dog/small/4.png',
        'pictures/dog/small/5.png',
        'pictures/dog/small/6.png',
        'pictures/dog/small/7.png',
        'pictures/dog/small/8.png',
        'pictures/dog/small/9.png'
    ],
    medium: [
        'pictures/dog/medium/1.png',
        'pictures/dog/medium/2.png',
        'pictures/dog/medium/3.png',
        'pictures/dog/medium/4.png',
        'pictures/dog/medium/5.png',
        'pictures/dog/medium/6.png',
        'pictures/dog/medium/7.png',
        'pictures/dog/medium/8.png',
        'pictures/dog/medium/9.png'
    ],
    large: [
        'pictures/dog/large/1.png',
        'pictures/dog/large/2.png',
        'pictures/dog/large/3.png',
        'pictures/dog/large/4.png',
        'pictures/dog/large/5.png',
        'pictures/dog/large/6.png',
        'pictures/dog/large/7.png',
        'pictures/dog/large/8.png',
        'pictures/dog/large/9.png'
    ],
    giant: [
        'pictures/dog/giant/1.png',
        'pictures/dog/giant/2.png',
        'pictures/dog/giant/3.png',
        'pictures/dog/giant/4.png',
        'pictures/dog/giant/5.png',
        'pictures/dog/giant/6.png',
        'pictures/dog/giant/7.png',
        'pictures/dog/giant/8.png',
        'pictures/dog/giant/9.png'
    ]
};

const catImages = [
    'pictures/cat/cat-1.png',
    'pictures/cat/cat-2.png',
    'pictures/cat/cat-3.png',
    'pictures/cat/cat-4.png',
    'pictures/cat/cat-5.png',
    'pictures/cat/cat-6.png',
    'pictures/cat/cat-7.png',
    'pictures/cat/cat-8.png',
    'pictures/cat/cat-9.png'
];

function updateAnimalInfo(animalType, score) {
    animalInfoContainer.innerHTML = ''; // Clear previous content

    const descriptions = scoreDescriptions[animalType];
    if (descriptions && descriptions[score]) {
        const titleElement = document.createElement('h3');
        titleElement.textContent = descriptions[score].title;
        animalInfoContainer.appendChild(titleElement);

        const descriptionList = document.createElement('ul');
        descriptions[score].description.forEach(item => {
            const listItem = document.createElement('li');
            listItem.textContent = item;
            descriptionList.appendChild(listItem);
        });
        animalInfoContainer.appendChild(descriptionList);
    } else {
        animalInfoContainer.textContent = 'Description not available.';
    }
}

function updateImage() {
    const selectedAnimal = animalTypeSelect.value;
    const score = slider.value;
    const imageDisplay = document.getElementById('imageDisplay');
    imageDisplay.innerHTML = ''; // Clear previous image

    let imagePath = '';
    let altText = `BCS Score ${score} (${selectedAnimal})`;

    if (selectedAnimal === 'cat') {
        imagePath = `pictures/cat/${score}.png`;
    } else if (selectedAnimal.startsWith('dog-')) {
        const dogSize = selectedAnimal.split('-')[1];
        imagePath = dogImages[dogSize][parseInt(score) - 1];
        altText = `BCS Score ${score} (Dog - ${dogSize})`;
    }

    const img = document.createElement('img');
    img.src = imagePath;
    img.alt = altText;
    img.style.maxWidth = '300px';
    img.style.height = 'auto';
    imageDisplay.appendChild(img);

    updateAnimalInfo(selectedAnimal.split('-')[0], score); // Envoie 'dog' ou 'cat' pour la description
    updateLabelPositions(); // Appeler la fonction pour positionner les labels
}

function updateLabelPositions() {
    const containerWidth = sliderContainer.offsetWidth;
    const min = parseInt(slider.min);
    const max = parseInt(slider.max);
    const range = max - min;
    const numLabels = scoreLabels.length;
    const offsets = [7, 2, 2, 1, 0, 0, -1, -1, -8]; // Décalages en pixels pour chaque label (le premier est +7)

    scoreLabels.forEach((label, index) => {
        const value = index + min;
        let position;
        const offset = offsets[index];

        if (index === 0) {
            position = offset;
            label.style.transform = 'translateX(0)';
            label.style.left = `${position}px`;
            label.style.textAlign = 'left';
        } else if (index === numLabels - 1) {
            position = containerWidth + offset;
            label.style.transform = 'translateX(0)';
            label.style.left = `${position}px`;
            label.style.textAlign = 'right';
        } else {
            position = ((value - min) / range) * containerWidth + (containerWidth / (numLabels - 1) * (offset / 20)); // Tentative de décalage proportionnel
            label.style.left = `${position}px`;
            label.style.transform = 'translateX(-50%)';
            label.style.textAlign = 'center';
        }
    });
}

animalTypeSelect.addEventListener('change', updateImage);
slider.addEventListener('input', updateImage);
window.addEventListener('resize', updateLabelPositions); // Recalculer si la fenêtre change de taille

// Initial setup
updateImage();
updateLabelPositions();