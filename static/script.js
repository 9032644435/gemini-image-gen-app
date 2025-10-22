const generateBtn = document.getElementById('generate-btn');
const promptInput = document.getElementById('prompt-input');
const generatedImage = document.getElementById('generated-image');

generateBtn.addEventListener('click', async () => {
    const prompt = promptInput.value;

    if (prompt) {
        try {
            const response = await fetch('/generate-image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt }),
            });

            if (response.ok) {
                const data = await response.json();
                generatedImage.src = data.image_url;
            } else {
                const errorData = await response.json();
                alert(`Error: ${errorData.error}`);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while generating the image.');
        }
    } else {
        alert('Please enter a prompt.');
    }
});
