"use client";

import type { DragEvent, ChangeEvent } from "react";
import { useEffect, useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { FilePlus2, LoaderIcon } from "lucide-react";
import Image from "next/image";
import mammoth from "mammoth";

const acceptedFileTypes = ["image/jpeg", "image/png", "image/webp"];

const formSchema = z.object({
    docType: z.string(),
});

const BACKEND_URL = "http://127.0.0.1:5000/process-image";

export default function Home() {
    const [file, setFile] = useState<File | null>(null);
    const [filePreview, setFilePreview] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [docxFile, setDocxFile] = useState<{
        blob: Blob;
        url: string;
        name: string;
    } | null>(null);
    const [loading, setLoading] = useState(false);
    const [HTMLContent, setHTMLContent] = useState<string>("");
    const [mammothErrorMessage, setMammothErrorMessage] = useState<string>("");

    const handleFileChange = (e: ChangeEvent<HTMLInputElement> | DragEvent<HTMLDivElement>) => {
        let uploadedFile;

        if (e instanceof DragEvent) {
            uploadedFile = e.dataTransfer?.files[0];
        }

        if (e.target instanceof HTMLInputElement) {
            uploadedFile = e.target.files?.[0];
        }

        if (uploadedFile) {
            console.log(`Dragging a ${uploadedFile.type} file over...`);

            if (!acceptedFileTypes.includes(uploadedFile.type)) {
                setErrorMessage("Only jpeg, png, and webp files are supported.");
                setFile(null);
                setFilePreview(null);
                return;
            }
            setErrorMessage(null);
            setFile(uploadedFile);

            if (uploadedFile.type.startsWith("image/")) {
                const reader = new FileReader();
                reader.onloadend = () => setFilePreview(reader.result as string);
                reader.readAsDataURL(uploadedFile);
            } else {
                setFilePreview(null);
            }
        }
    };

    const convertToHtml = async (blob: Blob) => {
        try {
            // Convert blob to arrayBuffer
            const arrayBuffer = await blob.arrayBuffer();

            // Use mammoth to convert DOCX to HTML
            const result = await mammoth.convertToHtml({ arrayBuffer });
            setHTMLContent(result.value);
        } catch (err) {
            console.error("Error converting DOCX to HTML:", err);
            setMammothErrorMessage("Failed to preview the document.");
        }
    };

    // Clean up object URLs when component unmounts
    useEffect(() => {
        return () => {
            if (docxFile?.url) {
                URL.revokeObjectURL(docxFile.url);
            }
        };
    }, [docxFile]);

    const downloadFile = () => {
        if (!docxFile) return;

        const a = document.createElement("a");
        a.href = docxFile.url;
        a.download = docxFile.name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    // 1. Define your form.
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            docType: "",
        },
    });

    // 2. Define a submit handler.
    async function onSubmit(values: z.infer<typeof formSchema>) {
        console.log("File: ", await file?.arrayBuffer());
        console.dir(values);
        toast.info("Your conversion request is being processed");
        // Send docType and file to back end
        setDocxFile(null);
        setLoading(true);
        setMammothErrorMessage("");
        try {
            if (!file) throw new Error("Please upload a file");
            const formData = new FormData();
            formData.append("values", JSON.stringify(values));
            formData.append("image", file);

            const response = await fetch(BACKEND_URL, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                throw new Error("Document generation failed");
            }

            const docxBlob = new Blob([await response.blob()], {
                type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            });

            const docxUrl = URL.createObjectURL(docxBlob);

            setDocxFile({
                blob: docxBlob,
                url: docxUrl,
                name: file.name.replace(/\.(jpg|jpeg|png)$/, ".docx"),
            });

            // Convert DOCX to HTML
            convertToHtml(docxBlob);
        } catch (error) {
            console.error(error);
            toast.error("Failed to generate document");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="grid grid-cols-2 items-center justify-items-center min-h-screen p-8 pb-20 gap-4 sm:p-20">
            <div className="flex gap-4 items-center flex-col h-full w-full">
                <div className="flex justify-center items-center w-full h-1/3 p-8 border rounded-lg">
                    <Form {...form}>
                        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
                            <FormField
                                control={form.control}
                                name="docType"
                                render={({ field }) => (
                                    <FormItem>
                                        <FormLabel>Document Type</FormLabel>
                                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                                            <FormControl>
                                                <SelectTrigger>
                                                    <SelectValue placeholder="Select the type of your document" />
                                                </SelectTrigger>
                                            </FormControl>
                                            <SelectContent>
                                                <SelectItem value="note">Notes</SelectItem>
                                                <SelectItem value="other">Other</SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <FormDescription>
                                            Please upload the photo you would like to convert before submitting
                                        </FormDescription>
                                        <FormMessage />
                                    </FormItem>
                                )}
                            />
                            <Button type="submit">Submit</Button>
                        </form>
                    </Form>
                </div>
                {!file ? (
                    <Label
                        htmlFor="file-upload"
                        className="cursor-pointer border border-dashed p-8 w-full h-2/3 flex flex-col items-center justify-center rounded-lg"
                    >
                        <div
                            onDrop={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                handleFileChange(e);
                            }}
                            onDragOver={(e) => {
                                e.preventDefault();
                                console.log("Dragging a file over...");
                            }}
                            className="flex flex-col items-center justify-center"
                        >
                            <FilePlus2 size={32} />
                            <div className="text-3xl font-bold">Upload Files</div>
                            <div>or drag and drop files here</div>
                            {errorMessage && <p className="text-red-500 mt-2">{errorMessage}</p>}
                        </div>
                        <input
                            id="file-upload"
                            type="file"
                            onChange={handleFileChange}
                            className="hidden"
                            accept=".jpg,.jpeg,.png"
                        />
                    </Label>
                ) : (
                    <div className="relative border p-8 w-full h-2/3 flex flex-col items-center justify-center rounded-lg">
                        {filePreview ? (
                            <Image
                                src={filePreview}
                                fill
                                alt="Uploaded Preview"
                                className="h-full aspect-auto object-contain"
                            />
                        ) : (
                            <p>{file.name}</p>
                        )}
                        <button
                            onClick={() => {
                                setFile(null);
                                setFilePreview(null);
                            }}
                            className="absolute bottom-4 mt-4 bg-red-500 text-white px-4 py-2 rounded-md"
                        >
                            Remove File
                        </button>
                    </div>
                )}
            </div>
            {/* Get doc output and display it */}
            <div className="flex flex-col justify-center items-center h-full w-full rounded-lg border">
                {!loading && !docxFile && <div>Your resuling document will appear here!</div>}
                {loading && (
                    <div className="p-4 animate-spin">
                        <LoaderIcon />
                    </div>
                )}
                {mammothErrorMessage && (
                    <div className="p-4 bg-red-100 text-red-700 rounded">{mammothErrorMessage}</div>
                )}
                {docxFile && (
                    <div className="p-4">
                        <div className="flex justify-between items-center">
                            <p>Document: {docxFile.name}</p>
                            <button
                                onClick={downloadFile}
                                className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600"
                            >
                                Download
                            </button>
                        </div>

                        <div>
                            <h3 className="font-bold mb-2">Preview:</h3>
                            {HTMLContent ? (
                                <div
                                    className="docx-preview aspect-[17/22] w-[480px] p-12 border overflow-y-scroll"
                                    dangerouslySetInnerHTML={{ __html: HTMLContent }}
                                />
                            ) : (
                                <p>Loading preview...</p>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}
