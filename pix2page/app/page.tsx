"use client";

import { useState } from "react";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { FilePlus2 } from "lucide-react";
import Image from "next/image";

const acceptedFileTypes = ["image/jpeg", "image/png", "image/webp"];

const formSchema = z.object({
    docType: z.string(),
});

export default function Home() {
    const [file, setFile] = useState<File | null>(null);
    const [filePreview, setFilePreview] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement> | React.DragEvent<HTMLDivElement>) => {
        let uploadedFile;
        if (e.dataTransfer) {
            uploadedFile = e.dataTransfer.files[0];
        } else {
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

    // 1. Define your form.
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            docType: "",
        },
    });

    // 2. Define a submit handler.
    function onSubmit(data: z.infer<typeof formSchema>) {
        // Do something with the form values.
        // ✅ This will be type-safe and validated.
        toast("You submitted the following values:", {
            description: (
                <pre className="mt-2 w-[340px] rounded-md bg-slate-950 p-4">
                    <code className="text-white">{JSON.stringify(data, null, 2)}</code>
                </pre>
            ),
        });
    }

    return (
        <main className="grid grid-cols-2 items-center justify-items-center min-h-screen p-8 pb-20 gap-4 sm:p-20">
            <div className="flex gap-4 items-center flex-col h-full w-full">
                <div className="flex justify-center items-center w-full h-1/3 border rounded-lg">
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
            <div className="flex justify-center items-center h-full w-full rounded-lg border">Doc Output</div>
        </main>
    );
}
