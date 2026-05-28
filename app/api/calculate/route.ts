import { NextResponse } from "next/server";
import { calculate, type CalcInput } from "@/lib/calculate";

export async function POST(req: Request) {
  try {
    const body = (await req.json()) as Partial<CalcInput>;
    const input: CalcInput = {
      itemPriceUsd: Number(body.itemPriceUsd ?? 0),
      originCountry: (body.originCountry ?? "JP") as CalcInput["originCountry"],
      category: (body.category ?? "general") as CalcInput["category"],
      actualWeightKg: Number(body.actualWeightKg ?? 1),
      lengthCm: Number(body.lengthCm ?? 30),
      widthCm: Number(body.widthCm ?? 20),
      heightCm: Number(body.heightCm ?? 10),
      jpyToUsd: Number(body.jpyToUsd ?? 155),
      includeShippingInDutyBase: body.includeShippingInDutyBase ?? true,
      section232: body.section232 ?? false,
      shippingMode: (body.shippingMode ?? "DIRECT") as CalcInput["shippingMode"],
    };
    const result = calculate(input);
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
